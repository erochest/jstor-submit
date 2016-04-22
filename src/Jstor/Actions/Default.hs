{-# LANGUAGE OverloadedStrings #-}


module Jstor.Actions.Default where


import           Control.Error

import           Jstor.Types


defaultAction :: FilePath -> [SearchTerm] -> Script ()
defaultAction _input _terms = undefined
