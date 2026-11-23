/*
 * Copyright 2026 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.example.jetnews

import androidx.activity.ComponentActivity
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.hasScrollAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToIndex
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.example.jetnews.data.posts.impl.post1
import com.example.jetnews.data.posts.impl.post5
import com.example.jetnews.ui.post.PostScreen
import com.example.jetnews.ui.post.minutesLeft
import com.example.jetnews.ui.theme.JetnewsTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@OptIn(ExperimentalTestApi::class)
@RunWith(AndroidJUnit4::class)
class ReadingProgressTests {

    @get:Rule
    val composeTestRule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun minutesLeft_roundsUpAndFinishesAtEnd() {
        assertEquals(4, minutesLeft(4, 0f))
        assertEquals(3, minutesLeft(4, 0.26f))
        assertEquals(1, minutesLeft(4, 0.99f))
        assertEquals(0, minutesLeft(4, 1f))
        assertEquals(1, minutesLeft(1, 0f))
        assertEquals(0, minutesLeft(1, 1f))
    }

    @Test
    fun scrollToEnd_showsFinished_backToTopResets() {
        composeTestRule.setContent {
            JetnewsTheme { PostScreen(post5, false, {}, false, {}, lazyListState = rememberLazyListState()) }
        }
        composeTestRule.onNodeWithText("4 min left").assertExists()
        composeTestRule.onNodeWithText("Back to top").assertDoesNotExist()

        composeTestRule.onNode(hasScrollAction()).performScrollToIndex(post5.paragraphs.size + 1)
        composeTestRule.onNodeWithText("Finished").assertExists()

        composeTestRule.onNodeWithText("Back to top").performClick()
        composeTestRule.waitUntilExactlyOneExists(hasText("4 min left"), 5000L)
        composeTestRule.waitUntilDoesNotExist(hasText("Back to top"), 5000L)
    }

    @Test
    fun oneMinutePost_startsAtOneMinute() {
        composeTestRule.setContent {
            JetnewsTheme { PostScreen(post1, false, {}, false, {}) }
        }
        composeTestRule.onNodeWithText("1 min left").assertExists()
    }
}
