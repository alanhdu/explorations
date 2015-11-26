pub mod expr {
    use std::ops::{Add, Sub, Mul, Div};
    use std::rc::Rc;

    #[derive(Debug, Clone)]
    pub struct Expr {
        expr: Rc<InnerExpr>
    }

    #[derive(Debug)]
    enum InnerExpr {
        Arithmetic(Arithmetic),
        Constant(f64),
    }

    impl Expr {
        pub fn constant(value: f64) -> Expr {
            Expr {expr: Rc::new(InnerExpr::Constant(value))}
        }

        pub fn eval(&self) -> f64 {
            self.expr.eval()
        }
    }

    impl InnerExpr {
        fn eval(&self) -> f64 {
            match *self {
                InnerExpr::Constant(x) => x,
                InnerExpr::Arithmetic(ref x) => x.eval(),
            }
        }
    }


    #[derive(Debug)]
    enum Arithmetic {
        Add(Rc<InnerExpr>, Rc<InnerExpr>),
        Sub(Rc<InnerExpr>, Rc<InnerExpr>),
        Mul(Rc<InnerExpr>, Rc<InnerExpr>),
        Div(Rc<InnerExpr>, Rc<InnerExpr>),
    }

    impl Arithmetic {
        fn eval(&self) -> f64 {
            match *self {
                Arithmetic::Add(ref a, ref b) => a.eval() + b.eval(),
                Arithmetic::Sub(ref a, ref b) => a.eval() - b.eval(),
                Arithmetic::Mul(ref a, ref b) => a.eval() * b.eval(),
                Arithmetic::Div(ref a, ref b) => a.eval() / b.eval(),
            }
        }
    }

    macro_rules! operator_overload {
        ($trait_name:ident, $struct_name:ident, $func_name:ident, $arith_type:ident) => {
            impl $trait_name<$struct_name> for $struct_name {
                type Output=$struct_name;
                fn $func_name(self, other: $struct_name) -> $struct_name {
                    let arithmetic = Arithmetic::$arith_type(self.expr.clone(),
                                                             other.expr.clone());
                    Expr {expr: Rc::new(InnerExpr::Arithmetic(arithmetic))}
                }
            }
            impl<'a> $trait_name for &'a $struct_name {
                type Output=$struct_name;
                fn $func_name(self, other: &'a $struct_name) -> $struct_name {
                    let arithmetic = Arithmetic::$arith_type(self.expr.clone(),
                                                             other.expr.clone());
                    Expr {expr: Rc::new(InnerExpr::Arithmetic(arithmetic))}
                }
            }
            impl<'a> $trait_name<&'a $struct_name> for $struct_name {
                type Output=$struct_name;
                fn $func_name(self, other: &'a $struct_name) -> $struct_name {
                    let arithmetic = Arithmetic::$arith_type(self.expr.clone(),
                                                             other.expr.clone());
                    Expr {expr: Rc::new(InnerExpr::Arithmetic(arithmetic))}
                }
            }
            impl<'a> $trait_name<$struct_name> for &'a $struct_name {
                type Output=$struct_name;
                fn $func_name(self, other: $struct_name) -> $struct_name {
                    let arithmetic = Arithmetic::$arith_type(self.expr.clone(),
                                                             other.expr.clone());
                    Expr {expr: Rc::new(InnerExpr::Arithmetic(arithmetic))}
                }
            }
        }
    }

    operator_overload!(Add, Expr, add, Add);
    operator_overload!(Sub, Expr, sub, Sub);
    operator_overload!(Mul, Expr, mul, Mul);
    operator_overload!(Div, Expr, div, Div);
}
