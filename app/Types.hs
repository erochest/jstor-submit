module Types where


import           Jstor.Types


data Actions
        = Default { defaultOutput :: !FilePath
                  , defaultTerms  :: ![SearchTerm]
                  }
        deriving (Show, Eq)
