pub mod expr {
    use std::ops::{Add, Sub};

    #[derive(Debug, Clone)]
    pub enum Expr {
        Arithmetic(Arithmetic),
        Constant(f64),
    }

    impl Expr {
        pub fn eval(&self) -> f64 {
            match self {
                &Expr::Constant(x) => x,
                &Expr::Arithmetic(ref x) => x.eval(),
            }
        }
    }


    #[derive(Debug, Clone)]
    pub enum Arithmetic {
        Add(Box<Expr>, Box<Expr>),
        Sub(Box<Expr>, Box<Expr>),
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
            Expr::Arithmetic(Arithmetic::Add(Box::new(self.clone()), Box::new(other.clone())))
        }
    }

    impl Sub for Expr {
        type Output = Expr;
        fn sub(self, other: Expr) -> Expr {
            Expr::Arithmetic(Arithmetic::Sub(Box::new(self.clone()), Box::new(other.clone())))
        }
    }
}
