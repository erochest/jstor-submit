{-# LANGUAGE OverloadedLists   #-}
{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE RecordWildCards   #-}


module Actions where


import           Control.Error

import           Jstor.Actions.Search

import           Types


action :: Actions -> Script ()

action Search{..} = searchAction searchOutput searchTerms
