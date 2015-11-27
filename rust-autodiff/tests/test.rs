extern crate autodiff;
extern crate quickcheck;

#[cfg(test)]
mod test {
    use autodiff::expr::Expr;
    use quickcheck::quickcheck;

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
    fn constant_add_eval() {
        fn prop(a: f64, b: f64) -> bool {
            let x = Expr::constant(a);
            let y = Expr::constant(b);

            (a + b) == (&x + &y).eval()
        }
        quickcheck(prop as fn(f64, f64) -> bool);
    }

    #[test]
    fn constant_sub_eval() {
        fn prop(a: f64, b: f64) -> bool {
            let x = Expr::constant(a);
            let y = Expr::constant(b);
            (a - b) == (&x - &y).eval()
        }
        quickcheck(prop as fn(f64, f64) -> bool);
    }
    #[test]
    fn constant_mul_eval() {
        fn prop(a: f64, b: f64) -> bool {
            let x = Expr::constant(a);
            let y = Expr::constant(b);
            (a * b) == (&x * &y).eval()
        }
        quickcheck(prop as fn(f64, f64) -> bool);
    }
    #[test]
    fn constant_div_eval() {
        fn prop(a: f64, b: f64) -> bool {
            let x = Expr::constant(a);
            let y = Expr::constant(b);
            (a / b) == (&x / &y).eval()
        }
        quickcheck(prop as fn(f64, f64) -> bool);
    }
    #[test]
    fn constant_complicated_eval() {
        fn prop(a: f64, b: f64) -> bool {
            let x = Expr::constant(a);
            let y = Expr::constant(b);
            (a + b * (a / (a - b))) == (&x + &y * (&x / (&x - &y))).eval()
        }
        quickcheck(prop as fn(f64, f64) -> bool);
    }
}
