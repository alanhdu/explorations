data Regex = Basic Char | Concat Regex Regex | Split Regex Regex | Repeat Regex deriving (Show, Eq, Read)

find :: Eq a => a -> [a] -> Integer
find x []     = 1
find x (y:ys) = if (==) x y then 0 else (+) 1 (find x ys)

addOne :: Integer -> Integer
addOne = (+) 1

-- Find closing parenthesis
{-
findClose :: [Char] -> Integer -> Integer
findClose ('(':str) level =  1 + (findClose str (level + 1))
findClose (c:str) level = 
-}



append :: a -> [a] -> [a]
append x []     = (:) x []
append x (y:ys) = (:) y (append x ys)

parse :: [Char] -> Regex
parse cs = foldl1 Concat (reverse (_parse cs []))

_parse :: [Char] -> [Regex] -> [Regex]
_parse "" rs = rs
_parse ('*':cs) (r:rs) = _parse cs ((:) (Repeat r) rs)

_parse ('|':cs) (r:rs) = new
    where ss     = reverse (_parse cs rs)
          first  = last ss
          others = init ss
          new    = (:) (Split r first) others

_parse ('(':cs) rs = _parse o n
    where f = fromIntegral (find ')' cs)
          t = take f cs
          o = tail (drop f cs)
          n = (:) (parse t) rs 

_parse cs rs = _parse (tail cs) n
    where n = (:) (Basic (head cs)) rs
