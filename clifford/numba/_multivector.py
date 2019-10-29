"""
Numba support for MultiVector objects.

For now, this just supports .value wrapping / unwrapping
"""
import numpy as np
import numba
from numba.extending import NativeValue

try:
    # module locations as of numba 0.49.0
    import numba.np.numpy_support as _numpy_support
    from numba.core.imputils import impl_ret_borrowed
    from numba.core import cgutils, types
except ImportError:
    # module locations prior to numba 0.49.0
    import numba.numpy_support as _numpy_support
    from numba.targets.imputils import impl_ret_borrowed
    from numba import cgutils, types

from .._multivector import MultiVector

from ._layout import LayoutType

__all__ = ['MultiVectorType']


class MultiVectorType(types.Type):
    def __init__(self, dtype: np.dtype):
        assert isinstance(dtype, np.dtype)
        self.dtype = dtype
        super().__init__(name='MultiVector[{!r}]'.format(numba.from_dtype(dtype)))

    @property
    def key(self):
        return self.dtype

    @property
    def value_type(self):
        return numba.from_dtype(self.dtype)[:]

    @property
    def layout_type(self):
        return LayoutType()


@numba.extending.typeof_impl.register(MultiVector)
def _typeof_MultiVector(val: MultiVector, c) -> MultiVectorType:
    return MultiVectorType(dtype=val.value.dtype)


@numba.extending.register_model(MultiVectorType)
class MultiVectorModel(numba.extending.models.StructModel):
    def __init__(self, dmm, fe_type):
        members = [
            ('layout', fe_type.layout_type),
            ('value', fe_type.value_type),
        ]
        super().__init__(dmm, fe_type, members)


@numba.extending.type_callable(MultiVector)
def type_MultiVector(context):
    def typer(layout, value):
        if isinstance(layout, LayoutType) and isinstance(value, types.Array):
            return MultiVectorType(_numpy_support.as_dtype(value.dtype))
    return typer


@numba.extending.lower_builtin(MultiVector, LayoutType, types.Any)
def impl_MultiVector(context, builder, sig, args):
    typ = sig.return_type
    layout, value = args
    mv = cgutils.create_struct_proxy(typ)(context, builder)
    mv.layout = layout
    mv.value = value
    return impl_ret_borrowed(context, builder, sig.return_type, mv._getvalue())


@numba.extending.unbox(MultiVectorType)
def unbox_MultiVector(typ: MultiVectorType, obj: MultiVector, c) -> NativeValue:
    value = c.pyapi.object_getattr_string(obj, "value")
    layout = c.pyapi.object_getattr_string(obj, "layout")
    mv = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    mv.layout = c.unbox(typ.layout_type, layout).value
    mv.value = c.unbox(typ.value_type, value).value
    c.pyapi.decref(value)
    c.pyapi.decref(layout)
    is_error = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(mv._getvalue(), is_error=is_error)


@numba.extending.box(MultiVectorType)
def box_MultiVector(typ: MultiVectorType, val: NativeValue, c) -> MultiVector:
    mv = cgutils.create_struct_proxy(typ)(c.context, c.builder, value=val)
    mv_obj = c.box(typ.value_type, mv.value)
    layout_obj = c.box(typ.layout_type, mv.layout)
    class_obj = c.pyapi.unserialize(c.pyapi.serialize_object(MultiVector))
    res = c.pyapi.call_function_objargs(class_obj, (layout_obj, mv_obj))
    c.pyapi.decref(mv_obj)
    c.pyapi.decref(class_obj)
    c.pyapi.decref(layout_obj)
    return res


numba.extending.make_attribute_wrapper(MultiVectorType, 'value', 'value')
numba.extending.make_attribute_wrapper(MultiVectorType, 'layout', 'layout')
