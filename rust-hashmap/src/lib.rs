use std::hash::{Hash, Hasher, SipHasher};

pub struct MapItem<T> {
    key: String,
    value: T
}

pub struct StringMap<T> {
    items: Vec<Option<MapItem<T>>>,
}

impl<T> StringMap<T> {
    pub fn new(size: usize) -> StringMap<T> {
        let mut items = Vec::with_capacity(size);

        for __ in 0..size {
            items.push(None);
        }

        StringMap {
            items: items,
        }
    }

    pub fn get_hash(&self, key: &str) -> usize {
        let mut hasher = SipHasher::default();
        key.hash(&mut hasher);
        return hasher.finish() as usize;
    }

    pub fn set(&mut self, key: &str, value: T) -> bool {
        let hash = self.get_hash(key);
        let len = self.items.len();

        for i in hash..(hash + len) {
            let index = i % len;
            let change = if let Some(ref item) = self.items[index] {
                item.key == key
            } else {
                true
            };

            if change {
                self.items[index] = Some(MapItem {
                    key: key.to_owned(),
                    value: value,
                });
                return true;
            }
        }

        false
    }

    pub fn get(&mut self, key: &str) -> Option<&T> {
        if let Some(index) = self.get_index(key) {
            if let Some(ref item) = self.items[index] {
                if item.key == key {
                    return Some(&item.value);
                }
            }
        }

        None
    }

    pub fn get_mut(&mut self, key: &str) -> Option<&mut T> {
        if let Some(index) = self.get_index(key) {
            if let Some(ref mut item) = self.items[index] {
                if item.key == key {
                    return Some(&mut item.value);
                }
            }
        }
        None
    }

    pub fn get_index(&self, key: &str) -> Option<usize> {
        let hash = self.get_hash(key);

        let len = self.items.len();
        for i in hash..(hash + len) {
            let index = i % len;
            if let Some(ref item) = self.items[index] {
                if item.key == key {
                    return Some(index);
                }
            }
        }
        None
    }

    pub fn delete(&mut self, key: &str) {
        if let Some(index) = self.get_index(key) {
            self.items[index] = None;
        }
    }

    pub fn load(&self) -> f64 {
        let load = self.items.iter()
            .filter(|item| item.is_some())
            .count();

        (load as f64) / (self.items.len() as f64)
    }
}

#[test]
fn test_load() {
    let mut h: StringMap<u32> = StringMap::new(5);

    assert!(h.set("hello", 5));
    assert_eq!(h.load(), 0.2);

    assert!(h.set("world", 6));
    assert_eq!(h.load(), 0.4);

    assert!(h.set("hello", 7));
    assert_eq!(h.load(), 0.4);

    h.delete("hello");
    assert_eq!(h.load(), 0.2);
}

#[test]
fn test_overload() {
    let mut h: StringMap<u32> = StringMap::new(1);

    assert!(0.0 == h.load());
    assert!(h.set("hello", 1));

    for i in 0..10 {
        assert!(!h.set(&i.to_string(), i));
        assert!(h.get(&i.to_string()).is_none());
        assert!(1.0 == h.load());
    }
}

#[test]
fn test_get_set() {
    let mut h: StringMap<u32> = StringMap::new(100);

    assert!(h.get("Not Found").is_none());

    assert!(h.set("hello", 5));
    assert_eq!(h.get("hello").unwrap(), &5);

    assert!(h.set("world", 100));
    assert_eq!(h.get("world").unwrap(), &100);

    assert!(h.set("hello", 0));
    assert_eq!(h.get("hello").unwrap(), &0);
}

#[test]
fn test_everything() {
    let mut h: StringMap<u32> = StringMap::new(100);

    for i in 1..101 {
        let key = i.to_string();
        assert!(h.set(&key, i));
        assert_eq!(h.get(&key).unwrap(), &i);

        assert_eq!(i as f64 / 100.0, h.load());
    }

    for i in 1..101 {
        h.delete(&i.to_string());
        assert!(h.get(&i.to_string()).is_none());
    }

    assert_eq!(0.0, h.load());
}
