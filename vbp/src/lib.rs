#[cfg(target_arch = "x86")]
use std::arch::x86::*;
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

const MAX: u64 = u64::max_value();
const MASKS: [[u64; 4]; 2] = [[0, 0, 0, 0], [MAX, MAX, MAX, MAX]];

#[allow(clippy::cast_ptr_alignment)]
unsafe fn loadu(src: &[u64; 4]) -> __m256i {
    _mm256_loadu_si256(src as *const _ as *const _)
}

#[allow(clippy::cast_ptr_alignment)]
unsafe fn storeu(dest: &mut [u64; 4], src: __m256i) {
    // loadu allows arbitrary alignment
    _mm256_storeu_si256(dest as *mut _ as *mut _, src);
}

pub fn pack(dest: &mut [[u64; 4]], src: &[usize]) {
    assert!(src.len() <= 256);
    debug_assert!((1..src.len()).all(|i| src[i] >= src[i - 1]));

    for (i, value) in src.iter().cloned().enumerate() {
        // Assert that we have enough bits
        dbg!(value);
        debug_assert_eq!(value >> dest.len(), 0);

        for (j, array) in dest.iter_mut().rev().enumerate() {
            let bit = ((1 << j) & value) != 0;
            array[i / 64] |= (bit as u64) << (i % 64);
        }
    }
    for i in src.len()..256 {
        let value = usize::max_value();
        for (j, array) in dest.iter_mut().rev().enumerate() {
            let bit = ((1 << j) & value) != 0;
            array[i / 64] |= (bit as u64) << (i % 64);
        }
    }
}

pub fn vbp_rank(src: &[[u64; 4]], mut needle: usize) -> usize {
    debug_assert_eq!(needle >> src.len(), 0);
    // Turn less_than_or_equal_to query into less_than

    needle <<= (8 * std::mem::size_of::<usize>()) - src.len();

    unsafe {
        let mut eq = _mm256_set1_epi64x(std::mem::transmute::<u64, i64>(MAX));
        let mut lt = _mm256_set1_epi64x(std::mem::transmute::<u64, i64>(0));

        // lt = lt | (eq & (!s & c))
        // eq = !(c ^ s) & eq
        for s in src.iter() {
            let s = loadu(s);
            let high_bit = needle >> ((8 * std::mem::size_of::<usize>()) - 1);
            let c = loadu(&MASKS[high_bit]);
            needle <<= 1;

            lt = _mm256_or_si256(
                lt,
                _mm256_and_si256(eq, _mm256_andnot_si256(s, c)),
            );
            eq = _mm256_andnot_si256(_mm256_xor_si256(c, s), eq);
        }

        let mut lte = [0; 4];
        storeu(&mut lte, _mm256_or_si256(lt, eq));
        let eq = {
            let mut tmp = [0; 4];
            storeu(&mut tmp, eq);
            tmp
        };

        // This should be equivalent code to:
        // if lte[2] != 0 {
        //     if lte[1] != 0 { 0 } else { 1 }
        // } else {
        //     if lte[3] != 0 { 2 } else { 3 }
        // }
        let mut index = 2 * (lte[2] != 0) as usize;
        index += (lte[index + 1] != 0) as usize;

        if eq[index] == 0 {
            (!lte[index]).trailing_zeros() as usize + index * 64
        } else {
            eq[index].trailing_zeros() as usize + index * 64
        }
    }
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_pack() {
        use std::iter::Extend;
        let mut values = (0..100).collect::<Vec<_>>();
        values.extend(vec![150; 10]);
        values.extend(200..346);
        assert_eq!(values.len(), 256);

        let mut expected: [[u64; 4]; 9] = [[0; 4]; 9];
        for i in 0..256 {
            for j in 0..9 {
                let bit = (1 << j) & values[i] != 0;
                if bit {
                    expected[8 - j][i / 64] |= 1 << (i % 64);
                }
            }
        }

        let mut columns: [[u64; 4]; 9] = [[0; 4]; 9];
        pack(&mut columns, &values);
        assert_eq!(columns, expected);
    }

    #[test]
    fn test_vbp_rank() {
        use std::iter::Extend;
        let mut values = (0..100).collect::<Vec<_>>();
        values.extend(vec![150; 10]);
        values.extend(200..346);
        assert_eq!(values.len(), 256);

        let mut columns: [[u64; 4]; 9] = [[0; 4]; 9];
        pack(&mut columns, &values);

        for i in 0..100 {
            assert_eq!(vbp_rank(&columns, i), i);
        }
        for i in 100..=150 {
            assert_eq!(vbp_rank(&columns, i), 100);
        }
        for i in 151..200 {
            assert_eq!(vbp_rank(&columns, i), 110);
        }
        for i in 200..346 {
            assert_eq!(vbp_rank(&columns, i), i - 90);
        }
    }
}
