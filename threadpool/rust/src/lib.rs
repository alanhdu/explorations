#![feature(fnbox)]
// Ugh... See https://github.com/rust-lang/rust/issues/28796
#![feature(conservative_impl_trait)]
// Well, if we have to use nightly, might as well...

extern crate crossbeam;
extern crate futures;

use std::thread;
use std::sync::Arc;
use std::boxed::FnBox;

use crossbeam::sync::MsQueue;
use futures::sync::oneshot;
use futures::Future as _Future;

pub struct ThreadPoolExecutor {
    channel: Arc<MsQueue<Message>>,
    threads: Option<Vec<thread::JoinHandle<()>>>,
}

enum Message {
    Run(Box<FnBox() -> () + Send>),
    Cancel,
}

pub trait Future {
    type Item;

    fn result(self) -> Self::Item;
}

struct InnerFuture<T> {
    recv: oneshot::Receiver<T>,
}

impl ThreadPoolExecutor {
    pub fn new(n: usize) -> ThreadPoolExecutor {
        let mut pool = ThreadPoolExecutor {
            channel: Arc::new(MsQueue::new()),
            threads: Some(Vec::with_capacity(n))
        };

        if let Some(ref mut threads) = pool.threads {
            for _ in 0..n {
                let channel = pool.channel.clone();
                let handle = thread::spawn(move || {
                    while let Message::Run(func) = channel.pop() {
                        func()
                    }
                });
                threads.push(handle)
            }
        }
        pool
    }

    pub fn submit<T, F>(&self, func: F) -> impl Future<Item=T>
        where F: FnOnce() -> T + Send + 'static,
              T: Send + 'static
    {
        let (send, recv) = oneshot::channel::<T>();

        let closure = Box::new(move || {
            send.complete(func());
        });
        self.channel.push(Message::Run(closure));

        InnerFuture {recv: recv}
    }

    pub fn shutdown(self) {
        unimplemented!()
    }
}

impl Drop for ThreadPoolExecutor {
    fn drop(&mut self) {
        let threads = self.threads.take().unwrap();
        for _ in 0..threads.len() {
            self.channel.push(Message::Cancel);
        }

        for thread in threads {
            thread.join().unwrap();
        }
    }
}

impl<T> Future for InnerFuture<T> {
    type Item = T;

    fn result(self) -> T {
        self.recv.wait().unwrap()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_constructor() {
        let pool = ThreadPoolExecutor::new(10);
        assert_eq!(Some(10), pool.threads.as_ref().map(|x| x.len()));
        assert!(pool.channel.is_empty());
    }
}
