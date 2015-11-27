pub mod expr {
    use std::collections::HashMap;
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
        Variable(String),
    }

    impl Expr {
        pub fn constant(value: f64) -> Expr {
            Expr {expr: Rc::new(InnerExpr::Constant(value))}
        }

        pub fn variable(name: &str) -> Expr {
            Expr {expr: Rc::new(InnerExpr::Variable(name.to_owned()))}
        }

        pub fn eval(&self, values: &HashMap<String, f64>) -> f64 {
            self.expr.eval(values)
        }

        pub fn forward_diff(&self, direction: &HashMap<String, f64>,
                            point: &HashMap<String, f64>) -> f64 {
            self.expr.forward_diff(direction, point)
        }
    }

    impl InnerExpr {
        fn eval(&self, values: &HashMap<String, f64>) -> f64 {
            match *self {
                InnerExpr::Constant(x) => x,
                InnerExpr::Arithmetic(ref x) => x.eval(values),
                InnerExpr::Variable(ref x) => *values.get(x).unwrap(),
            }
        }
        fn forward_diff(&self, direction: &HashMap<String, f64>,
                            point: &HashMap<String, f64>) -> f64 {
            match *self {
                InnerExpr::Constant(_) => 0.0,
                InnerExpr::Arithmetic(ref x) => x.forward_diff(direction, point),
                InnerExpr::Variable(ref x) => *direction.get(x).unwrap(),
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
        fn eval(&self, values: &HashMap<String, f64>) -> f64 {
            match *self {
                Arithmetic::Add(ref a, ref b) => a.eval(values) + b.eval(values),
                Arithmetic::Sub(ref a, ref b) => a.eval(values) - b.eval(values),
                Arithmetic::Mul(ref a, ref b) => a.eval(values) * b.eval(values),
                Arithmetic::Div(ref a, ref b) => a.eval(values) / b.eval(values),
            }
        }
        fn forward_diff(&self, direction: &HashMap<String, f64>,
                            point: &HashMap<String, f64>) -> f64 {
            match *self {
                Arithmetic::Add(ref a, ref b) => {
                    let lhs = a.forward_diff(direction, point);
                    let rhs = b.forward_diff(direction, point);
                    lhs + rhs
                },
                Arithmetic::Sub(ref a, ref b) => {
                    let lhs = a.forward_diff(direction, point);
                    let rhs = b.forward_diff(direction, point);
                    lhs - rhs
                }
                Arithmetic::Mul(ref a, ref b) => {
                    (a.eval(point) * b.forward_diff(direction, point) +
                        b.eval(point) * a.forward_diff(direction, point))
                }
                Arithmetic::Div(ref a, ref b) => {
                    let high= a.eval(point);
                    let low = b.eval(point);
                    let dhigh = a.forward_diff(direction, point);
                    let dlow = b.forward_diff(direction, point);

                    // low dhigh - high dlow, over denominator squared we go
                    (low * dhigh - high * dlow) / (low.powi(2))
                }
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
