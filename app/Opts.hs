{-# LANGUAGE LambdaCase #-}


module Opts
    ( Actions(..)
    , opts
    , execParser
    , parseOpts
    ) where


import qualified Data.Text           as T
import           Options.Applicative

import           Jstor.Types

import           Types


outputOpt :: Parser FilePath
outputOpt = strOption (  short 'o' <> long "output" <> metavar "OUTPUT_FILE"
                      <> help "The file to write back to.")

searchTermsOpts :: Parser [SearchTerm]
searchTermsOpts =
    some (argument (T.pack <$> str)
                   (  metavar "SEARCH_TERM" <> help "A term to search for."))

defaultOpts :: Parser Actions
defaultOpts = Default <$> outputOpt <*> searchTermsOpts

opts' :: Parser Actions
opts' = subparser
      (  command "default" (info (helper <*> defaultOpts)
                          (progDesc "Default action and options."))
      )

opts :: ParserInfo Actions
opts = info (helper <*> opts')
            (  fullDesc
            <> progDesc "Automate exporting stuff from jstor."
            <> header "jstor-submit - Automate exporting stuff from jstor.")

parseOpts :: IO Actions
parseOpts = execParser opts
