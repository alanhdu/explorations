extern crate autodiff;
#[macro_use] extern crate maplit;

#[cfg(test)]
mod test {
    use std::collections::HashMap;
    use std::f64::consts;
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
            assert_eq!(a.powf(b), (&x ^ &y).eval(&values));
            assert_eq!(a + b * (a / (a - b).powf(a)),
                       (&x + &y * (&x / ((&x - &y) ^ &x))).eval(&values));
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
            let values = hashmap!{"a".to_owned() => a, "b".to_owned() => b};

            assert_eq!(a + b, (&x + &y).eval(&values));
            assert_eq!(a - b, (&x - &y).eval(&values));
            assert_eq!(a * b, (&x * &y).eval(&values));
            assert_eq!(a / b, (&x / &y).eval(&values));
            assert_eq!(a.powf(b), (&x ^ &y).eval(&values));
            assert_eq!(a + b * (a / (a - b).powf(a)),
                       (&x + &y * (&x / ((&x - &y) ^ &x))).eval(&values));
        }
        prop(0.0, 1.0);
        prop(0.0, 5.0);
        prop(13.4, 5.0);
    }

    #[test]
    fn test_arithmetic_diff1() {
        fn prop(a: f64) {
            let x = Expr::variable("a");
            let direction = hashmap!{"a".to_owned() => 1.0};
            let values = hashmap!{"a".to_owned() => a};

            let expr = (&x + Expr::constant(10.0)) * (&x + Expr::constant(5.0));
            // D_x[expr] = D_x[x ** 2 + 15 x + 50] = 2x + 15
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
            let direction = hashmap!{"a".to_owned() => 1.0};
            let values = hashmap!{"a".to_owned() => a};

            let expr = (&x - Expr::constant(10.0)) / (&x * &x);
            // D_x[expr] = D_x[(x - 10) / x ** 2] = - 1 / x ** 2 + 20 / x ** 3
            assert_eq!(expr.forward_diff(&direction, &values),
                       -a.powi(-2) + 20.0 * a.powi(-3));
        }

        prop(1.0);
        prop(10.0);
        prop(0.34);
    }

    #[test]
    fn test_power_diff1() {
        fn prop(a: f64) {
            let x = Expr::variable("a");
            let direction = hashmap!{"a".to_owned() => 1.0};
            let values = hashmap!{"a".to_owned() => a};

            let expr = &x ^ Expr::constant(3.0);
            assert_eq!(expr.forward_diff(&direction, &values),
                       3.0 * a.powi(2));
        }

        prop(1.0);
        prop(10.0);
        prop(0.34);
    }

    #[test]
    fn test_power_diff2() {
        fn prop(a: f64) {
            let x = Expr::variable("a");
            let direction = hashmap!{"a".to_owned() => 1.0};
            let values = hashmap!{"a".to_owned() => a};

            let expr = Expr::constant(consts::E) ^ x;
            assert_eq!(expr.forward_diff(&direction, &values),
                       consts::E.powf(a));
        }

        prop(1.0);
        prop(10.0);
        prop(0.34);
    }

    #[test]
    fn test_power_nested_diff() {
        let x = Expr::variable("a");
        let values = hashmap!{"a".to_owned() => 1.0};

        let mut expr = &x ^ &x;
        for _ in 0..1000 {
            expr = expr ^ &x;
        }
        assert_eq!(expr.forward_diff(&values, &values), 1.0);
    }

    #[test]
    fn test_multi_direction_diff() {
        fn prop(a: f64, b: f64) {
            let x = Expr::variable("x");
            let y = Expr::variable("y");
            let diff_x = hashmap!{"x".to_owned() => 1.0, "y".to_owned() => 0.0};
            let diff_y = hashmap!{"x".to_owned() => 0.0, "y".to_owned() => 1.0};
            let expr = &x * &y + &x / &y;

            let values = hashmap!{"x".to_owned() => a, "y".to_owned() => b};
            // D_x[expr] = y + 1 / y
            assert_eq!(expr.forward_diff(&diff_x, &values),
                       b + 1.0 / b);
            // D_y[expr] = x - x / y **2
            assert_eq!(expr.forward_diff(&diff_y, &values),
                       a * (1.0 - b.powi(-2)));
        }

        prop(1.0, 2.0);
        prop(2.0, 2.0);
        prop(2.0, 5.0);
    }
}
