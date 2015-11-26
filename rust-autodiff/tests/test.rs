extern crate autodiff;


#[cfg(test)]
mod test {
    use autodiff::expr::Expr;

    #[test]
    fn constant_eval() {
        let a = Expr::Constant(10.0);
        let b = Expr::Constant(2.0);

        assert_eq!(a.eval(), 10.0);
        assert_eq!(b.eval(), 2.0);
        assert_eq!((&a + &b).eval(), 12.0);
        assert_eq!((&a + &b).eval(), 12.0);
    }
}
