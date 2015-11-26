pub mod expr {
    use std::ops::{Add, Sub};
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
            match self {
                &InnerExpr::Constant(x) => x,
                &InnerExpr::Arithmetic(ref x) => x.eval(),
            }
        }
    }


    #[derive(Debug)]
    enum Arithmetic {
        Add(Rc<InnerExpr>, Rc<InnerExpr>),
        Sub(Rc<InnerExpr>, Rc<InnerExpr>),
    }

    impl Arithmetic {
        fn eval(&self) -> f64 {
            match self {
                &Arithmetic::Add(ref a, ref b) => a.eval() + b.eval(),
                &Arithmetic::Sub(ref a, ref b) => a.eval() - b.eval(),
            }
        }
    }


    impl<'a> Add for &'a Expr {
        type Output = Expr;
        fn add(self, other: &'a Expr) -> Expr {
            let lhs = self.expr.clone();
            let rhs = other.expr.clone();
            let inner_expr = InnerExpr::Arithmetic(Arithmetic::Add(lhs, rhs));

            Expr {expr: Rc::new(inner_expr)}
        }
    }

    impl<'a> Add<Expr> for &'a Expr {
        type Output = Expr;
        fn add(self, other: Expr) -> Expr {
            let lhs = self.expr.clone();
            let rhs = other.expr.clone();
            let inner_expr = InnerExpr::Arithmetic(Arithmetic::Add(lhs, rhs));

            Expr {expr: Rc::new(inner_expr)}
        }
    }

    impl Add for Expr {
        type Output = Expr;
        fn add(self, other: Expr) -> Expr {
            let lhs = self.expr.clone();
            let rhs = other.expr.clone();
            let inner_expr = InnerExpr::Arithmetic(Arithmetic::Add(lhs, rhs));

            Expr {expr: Rc::new(inner_expr)}
        }
    }

    impl<'a> Add<&'a Expr> for Expr {
        type Output = Expr;
        fn add(self, other: &'a Expr) -> Expr {
            let lhs = self.expr.clone();
            let rhs = other.expr.clone();
            let inner_expr = InnerExpr::Arithmetic(Arithmetic::Add(lhs, rhs));

            Expr {expr: Rc::new(inner_expr)}
        }
    }

    impl<'a> Sub for &'a Expr {
        type Output = Expr;
        fn sub(self, other: &'a Expr) -> Expr {
            let lhs = self.expr.clone();
            let rhs = other.expr.clone();
            let inner_expr = InnerExpr::Arithmetic(Arithmetic::Sub(lhs, rhs));

            Expr {expr: Rc::new(inner_expr)}
        }
    }
}
