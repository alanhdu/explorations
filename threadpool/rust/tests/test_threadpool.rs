extern crate threadpool;

use threadpool::*;

#[test]
fn test_basic_submit() {
    let pool = ThreadPoolExecutor::new(1);
    let future = pool.submit(|| 1);

    assert_eq!(1, future.result());
}

#[test]
fn test_big_submit() {
    let pool = ThreadPoolExecutor::new(8);

    let mut futures = Vec::with_capacity(1000);
    for i in 0..1000 {
        futures.push(pool.submit(move || i));
    }

    for (i, future) in futures.into_iter().enumerate() {
        assert_eq!(i, future.result());
    }
}
