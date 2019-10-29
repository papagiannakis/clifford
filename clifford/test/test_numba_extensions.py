import numba

from clifford.g3c import layout, e1, e2
import clifford as cf


@numba.njit
def identity(x):
    return x


class TestBasic:
    """ Test very simple construction and field access """

    def test_roundtrip_layout(self):
        layout_r = identity(layout)
        assert type(layout_r) is type(layout)
        assert layout_r is layout

    def test_roundtrip_mv(self):
        e1_r = identity(e1)
        assert type(e1_r) is type(e1_r)

        # mvs are values, and not preserved by identity
        assert e1_r.layout is e1.layout
        assert e1_r == e1

    def test_piecewise_construction(self):
        @numba.njit
        def negate(a):
            return cf.MultiVector(a.layout, -a.value)

        n_e1 = negate(e1)
        assert n_e1.layout is e1.layout
        assert n_e1 == -e1

        @numba.njit
        def add(a, b):
            return cf.MultiVector(a.layout, a.value + b.value)

        ab = add(e1, e2)
        assert ab == e1 + e2
        assert ab.layout is e1.layout
