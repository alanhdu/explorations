extern crate threadpool;

use std::thread;
use std::time;
use std::sync;

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

#[test]
fn test_shutdown() {
    let (send, recv) = sync::mpsc::channel();

    thread::spawn(move || {
        {
            let pool = ThreadPoolExecutor::new(8);
            for _ in 0..10000 {
                pool.submit(move || {
                    thread::sleep(time::Duration::from_millis(50));
                });
            }
            pool.shutdown();
        }
        send.send(()).unwrap();
    });

    recv.recv_timeout(time::Duration::from_millis(100)).unwrap();
}
