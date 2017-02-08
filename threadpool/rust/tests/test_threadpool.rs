#![feature(conservative_impl_trait)]

extern crate futures;
extern crate threadpool;

use std::thread;
use std::time;
use std::sync;

use futures::Future;
use futures::sync::oneshot;

use threadpool::*;

#[test]
fn test_basic_submit() {
    let pool = ThreadPoolExecutor::new(1);
    let future = pool.submit(|| 1);

    assert_eq!(Ok(1), future.wait());
}

#[test]
fn test_big_submit() {
    let pool = ThreadPoolExecutor::new(8);

    let mut futures = Vec::with_capacity(1000);
    for i in 0..1000 {
        futures.push(pool.submit(move || i));
    }

    for (i, future) in futures.into_iter().enumerate() {
        assert_eq!(Ok(i), future.wait());
    }
}

#[test]
fn test_shutdown() {
    let (send, recv) = sync::mpsc::channel();

    thread::spawn(move || {
        {
            let pool = ThreadPoolExecutor::new(1);
            for _ in 0..10 {
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

#[test]
fn test_cancel() {
    let pool = ThreadPoolExecutor::new(0);
    let mut future = pool.submit(move || 1);
    pool.shutdown();

    assert_eq!(Err(oneshot::Canceled), future.poll());
    assert_eq!(Err(oneshot::Canceled), future.wait());
}
