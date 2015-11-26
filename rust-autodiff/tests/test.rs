extern crate autodiff;


#[cfg(test)]
mod test {
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
        let a = Expr::constant(10.0);
        let b = Expr::constant(2.0);

        assert_eq!(a.eval(), 10.0);
        assert_eq!(b.eval(), 2.0);
        assert_eq!((&a + &b).eval(), 12.0);
        assert_eq!((&a + &a + &a).eval(), 30.0);
        assert_eq!(((&a + &a) + (&a + &a)).eval(), 40.0);
        assert_eq!((&a - &b).eval(), 8.0);
    }
}
