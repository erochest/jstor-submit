module Types where


import           Jstor.Types


data Actions
        = Search
        { searchOutput :: !FilePath
        , searchTerms  :: ![SearchTerm]
        }
        deriving (Show, Eq)
