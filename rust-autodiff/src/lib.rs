pub mod expr {
    use std::collections::HashMap;
    use std::ops::{Add, Sub, Mul, Div, BitXor};
    use std::rc::Rc;

    /// User-facing wrapper for `Rc<InnerExpr>`
    ///
    /// Use `Rc` because we want shared ownership of immutable `InnerExpr`s.
    /// That way, we can just `clone` the `Rc` instead of `clone`-ing the entire
    /// `InnerExpr` enum.
    #[derive(Debug, Clone)]
    pub struct Expr {
        expr: Rc<InnerExpr>
    }

    impl Expr {
        /// Constructor to represent a constant `Expr`
        pub fn constant(value: f64) -> Expr {
            Expr {expr: Rc::new(InnerExpr::Constant(value))}
        }

        /// Constructor for an `Expr` variable
        pub fn variable(name: &str) -> Expr {
            Expr {expr: Rc::new(InnerExpr::Variable(name.to_owned()))}
        }

        /// Evaluate the `expr` at the point given at `values`.
        ///
        /// `values` should map variable name to the value (e.g. {"x" => 1}). We
        /// don't do any error-handling, so if a variable name is not in
        /// `values`, we panic. TODO: actual error handling.
        pub fn eval(&self, values: &HashMap<String, f64>) -> f64 {
            self.expr.eval(values)
        }

        /// Evaluate the directional derivative of the `Expr` at the point
        /// `point` in the direction of `direction`. In other words, it computes
        /// the dot product of the gradient of Expr @ point with direction.
        ///
        /// Both `point` and `direction` should map variable names to their
        /// values. Again, there's no intelligent error handling if a variable
        /// is not found.
        pub fn forward_diff(&self, direction: &HashMap<String, f64>,
                            point: &HashMap<String, f64>) -> f64 {
            self.expr.forward_diff(direction, point)
        }
    }

    /// Private type that handles the actual heavy-lifting.
    ///
    /// We separate Arithmetic out as a separate type to increase modularity. In
    /// retrospect, this probably wasn't worth the added verbosity.
    #[derive(Debug)]
    enum InnerExpr {
        Arithmetic(Arithmetic),
        Constant(f64),
        Variable(String),
    }

    /// See documentation for `impl Expr`
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


    /// Represents basic arithmetic between expressions. Use reference counted
    /// pointers for shared ownership of the `InnerExpr`s.
    #[derive(Debug)]
    enum Arithmetic {
        Add(Rc<InnerExpr>, Rc<InnerExpr>),
        Sub(Rc<InnerExpr>, Rc<InnerExpr>),
        Mul(Rc<InnerExpr>, Rc<InnerExpr>),
        Div(Rc<InnerExpr>, Rc<InnerExpr>),
        Pow(Rc<InnerExpr>, Rc<InnerExpr>),
    }

    impl Arithmetic {
        fn eval(&self, values: &HashMap<String, f64>) -> f64 {
            match *self {
                Arithmetic::Add(ref a, ref b) => a.eval(values) + b.eval(values),
                Arithmetic::Sub(ref a, ref b) => a.eval(values) - b.eval(values),
                Arithmetic::Mul(ref a, ref b) => a.eval(values) * b.eval(values),
                Arithmetic::Div(ref a, ref b) => a.eval(values) / b.eval(values),
                Arithmetic::Pow(ref a, ref b) => a.eval(values).powf(b.eval(values)),
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
                },
                Arithmetic::Mul(ref a, ref b) => {
                    (a.eval(point) * b.forward_diff(direction, point) +
                        b.eval(point) * a.forward_diff(direction, point))
                },
                Arithmetic::Div(ref a, ref b) => {
                    let high= a.eval(point);
                    let low = b.eval(point);
                    let dhigh = a.forward_diff(direction, point);
                    let dlow = b.forward_diff(direction, point);

                    // low dhigh - high dlow, over denominator squared we go
                    (low * dhigh - high * dlow) / (low.powi(2))
                },
                Arithmetic::Pow(ref a, ref b) => {
                    // D_x[f ** g] = D_x[exp(g ln f)] = exp(g ln f) D_x[g ln f]
                    //             = exp(g ln f) (gf' / f + g' ln f)
                    //             = f ** g * (gf' / f + g' ln f)
                    //             = f ** (g - 1) * (gf' + fg' ln f)
                    // Verified by WolframAlpha :)
                    let base = a.eval(point);
                    let exp = b.eval(point);
                    let dbase = a.forward_diff(direction, point);
                    let dexp = b.forward_diff(direction, point);

                    if base == 0.0 {    // avoid divide by zero error
                        0.0
                    } else {
                        base.powf(exp - 1.0) * (exp * dbase + base * dexp * base.ln())
                    }
                }
            }
        }
    }

    /// Macro for easy operator overloading.
    ///
    /// The only difference between the difference operator overloading are the
    /// trait names (Add vs Sub), the name of the function (add vs sub), and the
    /// variant of Arithmetic that we use (Arithmetic::Pow vs Arithmetic::Sub),
    /// so we abstract the logic into a macro to reduce repetition.
    ///
    /// NOTE: Operator overloading in Rust takes things by value, we need to be
    /// careful to do our arithmetic by references. Unfortunately, because of
    /// how ownership works, we need to implement the same logic for
    /// (Value, Value), (Value, Ref), (Ref, Ref), and (Ref, Value). For example:
    ///     ```
    ///     let a = Expr::constant(3.0);
    ///     let b = Expr::constant(4.0);
    ///
    ///     let c = a + b;  // ownership of a and b are moved
    ///     let d = a + b;  // so this fails
    ///     ```
    /// Instead, we can do:
    ///     ```
    ///     let a = Expr::constant(3.0);
    ///     let b = Expr::constant(4.0);
    ///
    ///     let c = &a + &b;  // Ref + Ref
    ///     let d = &a + &b;  // Because Add takes references, no ownership problems
    ///     (&a + &a) + &a;         // (Ref + Ref) + Ref -> Value + Ref
    ///     &a + (&a + &a);         // Ref + (Ref + Ref) -> Ref + Value
    ///     (&a + &a) + (&a + &a)   // (Ref + Ref) + (Ref + Ref) -> Value + Value
    ///     ```
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
    operator_overload!(BitXor, Expr, bitxor, Pow);
}
