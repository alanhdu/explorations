extern crate autodiff;

#[cfg(test)]
mod test {
    use std::collections::HashMap;
    use autodiff::expr::Expr;

    #[test]
    fn operator_chaining() {
        let a = Expr::constant(10.0);
        (&a + &a) + (&a + &a);      // Value + Value, Ref + Ref
        (&a + &a) + &a;             // Value + Ref
        &a + (&a + &a);             // Ref + Value

        (&a - &a) - (&a - &a);      // Value - Value, Ref - Ref
        (&a - &a) - &a;             // Value - Ref
        &a - (&a - &a);             // Ref - Value

        (&a * &a) * (&a * &a);      // Value * Value, Ref * Ref
        (&a * &a) * &a;             // Value * Ref
        &a * (&a * &a);             // Ref * Value

        (&a / &a) / (&a / &a);      // Value / Value, Ref / Ref
        (&a / &a) / &a;             // Value / Ref
        &a / (&a / &a);             // Ref / Value
    }

    #[test]
    fn constant_eval() {
        fn prop(a: f64, b: f64) {
            let x = Expr::constant(a);
            let y = Expr::constant(b);
            let values = HashMap::new();

            assert_eq!(a + b, (&x + &y).eval(&values));
            assert_eq!(a - b, (&x - &y).eval(&values));
            assert_eq!(a * b, (&x * &y).eval(&values));
            assert_eq!(a / b, (&x / &y).eval(&values));
            assert_eq!(a + b * (a / (a - b)),
                       (&x + &y * (&x / (&x - &y))).eval(&values));
        }
        prop(0.0, 1.0);
        prop(0.0, 5.0);
        prop(13.4, 5.0);
    }

    #[test]
    fn variable_eval() {
        fn prop(a: f64, b: f64) {
            let x = Expr::variable("a");
            let y = Expr::variable("b");
            let mut values = HashMap::new();
            values.insert("a".to_owned(), a);
            values.insert("b".to_owned(), b);

            assert_eq!(a + b, (&x + &y).eval(&values));
            assert_eq!(a - b, (&x - &y).eval(&values));
            assert_eq!(a * b, (&x * &y).eval(&values));
            assert_eq!(a / b, (&x / &y).eval(&values));
            assert_eq!(a + b * (a / (a - b)),
                       (&x + &y * (&x / (&x - &y))).eval(&values));
        }
        prop(0.0, 1.0);
        prop(0.0, 5.0);
        prop(13.4, 5.0);
    }

    #[test]
    fn test_arithmetic_diff1() {
        fn prop(a: f64) {
            let x = Expr::variable("a");
            let mut direction = HashMap::new();
            let mut values = HashMap::new();
            direction.insert("a".to_owned(), 1.0);
            values.insert("a".to_owned(), a);

            let expr = (&x + Expr::constant(10.0)) * (&x + Expr::constant(5.0));
            // D_x[expr] = D_x[x ** 2 + 15 x + 50] = 2x + 15
            // a
            assert_eq!(expr.forward_diff(&direction, &values),
                       2.0 * a + 15.0);
        }
        prop(1.0);
        prop(10.0);
        prop(23.4);
    }

    #[test]
    fn test_arithmetic_diff2() {
        fn prop(a: f64) {
            let x = Expr::variable("a");
            let mut direction = HashMap::new();
            let mut values = HashMap::new();
            direction.insert("a".to_owned(), 1.0);
            values.insert("a".to_owned(), a);

            let expr = (&x + Expr::constant(10.0)) / (&x * &x);
            // D_x[expr] = D_x[(x + 10) / x ** 2] = - 1 / x ** 2 - 20 / x ** 3
            assert_eq!(expr.forward_diff(&direction, &values),
                       -a.powi(-2) - 20.0 * a.powi(-3));
        }

        prop(1.0);
        prop(10.0);
        prop(23.4);
    }
}
