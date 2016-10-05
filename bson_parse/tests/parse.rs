extern crate bson_parse;

#[macro_use]
extern crate bson;
extern crate nom;
extern crate chrono;

use bson::Bson;
use bson_parse::nom_doc;
use chrono::TimeZone;

#[test]
fn test_parse_empty_document() {
    let doc = doc!();

    let mut buf = Vec::new();
    bson::encode_document(&mut buf, &doc).unwrap();

    if let nom::IResult::Done(b"", output) = nom_doc(&buf) {
        assert_eq!(output, doc);
    } else {
        unreachable!();
    }
}

#[test]
fn test_parse_javascript_closure() {
    let doc = doc!{
    };

    let mut buf = Vec::new();
    bson::encode_document(&mut buf, &doc).unwrap();

    println!("{:?}", &buf);
    if let nom::IResult::Done(b"", output) = nom_doc(&buf) {
        assert_eq!(doc, output);
    } else {
        unreachable!();
    }
}

#[test]
fn test_parse_complex_document() {
    let doc = doc!{
        "string" => "hello",
        "float" => 2.718281828,
        "doc" => (doc!{
            "nested" => "three"
        }),
        "array" => (vec![bson!("hellO"), bson!(1), bson!(doc!{})]),
        "object id" => (bson::oid::ObjectId::with_bytes(*b"123456789ABC")),
        "false" => false,
        "true" => true,
        "date" => (chrono::UTC.timestamp(1473582027, 2000000)),
        "null" => (bson::Bson::Null),
        "i32" => (34 as i32),
        "i64" => (64 as i64),
        "regexp" => (Bson::RegExp("hello".to_string(), "world".to_string())),
        "timestamp" => (Bson::TimeStamp(95)),
        "javascript" => (Bson::JavaScriptCode("console.log('hello world!')".to_string()))
            // Bson::JavaScriptCodeWithScope has a bug in it, so this doesn't work.
        // "a" => (Bson::JavaScriptCodeWithScope("console.log(x)".to_string(), doc!{"x" => "hello"}))
    };

    let mut buf = Vec::new();
    bson::encode_document(&mut buf, &doc).unwrap();

    println!("{:?}", &buf);
    if let nom::IResult::Done(b"", output) = nom_doc(&buf) {
        assert_eq!(doc, output);
    } else {
        unreachable!();
    }
}
