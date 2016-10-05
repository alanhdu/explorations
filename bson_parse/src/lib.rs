extern crate bson;
extern crate chrono;
#[macro_use]
extern crate nom;

use std::iter::FromIterator;

use bson::{Bson, Document};
use chrono::TimeZone;
use nom::IResult;


named!(pub nom_doc<Document>,
       complete!(
           map_opt!(
               // First byte is total length. Rest of doc is length - sizeof(i32)
               length_bytes!(map!(nom::le_i32, |x| x - 4)),
               |bytes: &[u8]| {
                   if let Some((&0x00, init)) = bytes.split_last() {
                       if let IResult::Done(b"", output) = element_list(init) {
                           return Some(output);
                       }
                   }
                   return None;
               }
               )
           ));

named!(element_list<Document>,
       map!(many0!(element), bson::ordered::OrderedDocument::from_iter)
      );

    named!(element<(String, Bson)>,
    alt_complete!(
        preceded!(
            tag!(b"\x01"),
            pair!(cstring, map!(nom::le_f64, Bson::FloatingPoint)))
        | preceded!(
            tag!(b"\x02"),
            pair!(cstring, map!(string, Bson::String)))
        | preceded!(
            tag!(b"\x03"),
            pair!(cstring, map!(nom_doc, Bson::Document)))
        | preceded!(
            tag!(b"\x04"),
            // For some reason, arrays are actually stored as documents.
            pair!(cstring, map_opt!(nom_doc, doc_to_array)))
        | preceded!(
            tag!(b"\x05"),
            pair!(cstring, binary))
        | preceded!(
            tag!(b"\x07"),
            pair!(cstring, objectid))
        | preceded!(
            tag!(b"\x08"),
            pair!(cstring, map_opt!(nom::be_u8, |x: u8| {
                match x {
                    0 => Some(Bson::Boolean(false)),
                    1 => Some(Bson::Boolean(true)),
                    _ => None
                }
            })))
| preceded!(
    tag!(b"\x09"),
    pair!(cstring, map!(nom::le_i64, |x: i64| {
        let s = x / 1000;
        let ns = (x % 1000) as u32 * 1000000;
        Bson::UtcDatetime(chrono::UTC.timestamp(s, ns))
    })))
| preceded!(
    tag!(b"\x0A"),
    map!(cstring, |name| (name, Bson::Null)))
| preceded!(
    tag!(b"\x0B"),
    pair!(cstring, map!(pair!(cstring, cstring), |(x, y)| Bson::RegExp(x, y))))
| preceded!(
    tag!(b"\x0D"),
    pair!(cstring, map!(string, Bson::JavaScriptCode)))
| preceded!(
    tag!(b"\x0F"),
    pair!(cstring,
          map_res!(
              chain!(
                  // - 4 for length of int32
                  bytes: length_bytes!(map!(nom::le_i32, |x| x - 4)),
                  || {
                      match complete!(bytes, pair!(string, nom_doc)) {
                          IResult::Done(b"", (s, doc)) => Ok(Bson::JavaScriptCodeWithScope(s, doc)),
                          IResult::Error(err) => Err(err),
                          _ => panic!("Unreachable because of complete!")
                      }
                  }
                  ),
                  |x| x)))
| preceded!(
    tag!(b"\x10"),
    pair!(cstring, map!(nom::le_i32, Bson::I32)))
| preceded!(
    tag!(b"\x11"),
    pair!(cstring, map!(nom::le_i64, Bson::TimeStamp)))
| preceded!(
    tag!(b"\x12"),
    pair!(cstring, map!(nom::le_i64, Bson::I64)))
// For some reason, bson doesn't support MinKey or MaxKey
));

named!(string<String>, map_opt!(
        length_bytes!(nom::le_i32),
        |bytes: &[u8]| {
            if let Some((&0x00, init)) = bytes.split_last() {
                String::from_utf8(init.to_vec()).ok()
            } else {
                None
            }
        }
        ));

named!(binary<Bson>,
       map_opt!(
           length_bytes!(map!(nom::le_i32, |x| x + 1)),
           bytes_to_binary
           ));
named!(objectid<Bson>,
       map_opt!(
           take!(12),
           |bytes: &[u8]| {
               // copy the slice into a sized array
               let mut iter = bytes.iter();
               let mut array = [0; 12];
               for x in &mut array {
                   if let Some(byte) = iter.next() {
                       *x = *byte
                   } else {
                       return None
                   }
               }
               Some(Bson::ObjectId(bson::oid::ObjectId::with_bytes(array)))
           }));


named!(cstring<String>,
       map_res!(
           take_until_and_consume!(b"\0"),
           |x: &[u8]| {
               String::from_utf8(x.to_vec())
           }
           ));

fn bytes_to_binary(bytes: &[u8]) -> Option<Bson> {
    use bson::spec::*;
    match bytes.split_first() {
        Some((&subtype @ 0x00...0x05, rest)) |
            Some((&subtype @ 0x80, rest)) => {
                Some(Bson::Binary(BinarySubtype::from(subtype), rest.to_vec()))
            }
        _ => None,
    }
}

fn doc_is_array(doc: &Document) -> bool {
    doc.keys()
        .enumerate()
        .all(|(i, key)| Ok(i) == key.parse::<usize>())
}

fn doc_to_array(doc: Document) -> Option<Bson> {
    if doc_is_array(&doc) {
        Some(Bson::Array(doc.into_iter().map(|(_, y)| y).collect()))
    } else {
        None
    }
}


#[test]
fn test_cstring() {
    if let IResult::Done(remaining, output) = cstring(b"Hello\0world!") {
        assert_eq!(remaining, b"world!");
        assert_eq!(output, "Hello");
    } else {
        unreachable!()
    }
}

#[test]
fn test_binary() {
    let mut bytes = b"\x05\0\0\0\x011234567";
    if let IResult::Done(remaining, output) = binary(bytes) {
        assert_eq!(output, Bson::Binary(bson::spec::BinarySubtype::Function,
                                        b"12345".to_vec()));
        assert_eq!(remaining, b"67");
    } else {
        unreachable!();
    }

    // Invalid subtype
    bytes = b"\x05\0\0\0\x321234567";
    if let IResult::Error(_) = binary(bytes) {
    } else {
        unreachable!();
    }
}

#[test]
fn test_string() {
    let mut bytes = b"\x06\0\0\012345\067";
    if let IResult::Done(remaining, output) = string(bytes) {
        assert_eq!(output, "12345");
        assert_eq!(remaining, b"67");
    } else {
        unreachable!();
    }

    // Not terminated with null byte
    bytes = b"\x05\0\0\012345678";
    if let IResult::Error(_) = binary(bytes) {
    } else {
        unreachable!();
    }
}

#[test]
fn test_element_floating_point() {
    let tmp: [u8; 8] = unsafe{std::mem::transmute_copy(&3.1415)};
    let mut bytes = b"\x01hello\0".to_vec();
    bytes.extend(&tmp);

    if let IResult::Done(remaining, output) = element(&bytes) {
        assert_eq!(output, ("hello".to_string(), Bson::FloatingPoint(3.1415)));
        assert_eq!(remaining, b"");
    } else {
        unreachable!();
    }
}

#[test]
fn test_element_string() {
    let bytes = b"\x02string\0\x06\0\0\0hello\0";
    if let IResult::Done(remaining, output) = element(bytes) {
        assert_eq!(output, ("string".to_string(), Bson::String("hello".to_string())));
        assert_eq!(remaining, b"");
    } else {
        unreachable!();
    }
}

#[test]
fn test_element_int() {
    let bytes = b"\x1012345\0\x05\0\0\0";
    if let IResult::Done(remaining, output) = element(bytes) {
        assert_eq!(output, ("12345".to_string(), Bson::I32(5)));
        assert_eq!(remaining, b"");
    } else {
        unreachable!();
    }
}
