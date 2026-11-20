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

package com.example.jetnews.ui.post

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.hasScrollToIndexAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToIndex
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.example.jetnews.data.posts.impl.post5
import com.example.jetnews.ui.theme.JetnewsTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@OptIn(ExperimentalTestApi::class)
@RunWith(AndroidJUnit4::class)
class PostReadingProgressTest {

    @get:Rule
    val composeTestRule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun minutesLeft_roundsUp() {
        assertEquals(1, minutesLeft(1, 0f))
        assertEquals(0, minutesLeft(1, 1f))
        assertEquals(4, minutesLeft(4, 0.2f))
        assertEquals(1, minutesLeft(4, 0.9f))
    }

    @Test
    fun progress_countsDownAndBackToTopReturns() {
        composeTestRule.setContent {
            JetnewsTheme {
                PostScreen(post5, isExpandedScreen = false, onBack = {}, isFavorite = false, onToggleFavorite = {})
            }
        }
        composeTestRule.onNodeWithText("4 min left").assertExists()
        composeTestRule.onNodeWithText("Back to top", useUnmergedTree = true).assertDoesNotExist()

        composeTestRule.onNode(hasScrollToIndexAction()).performScrollToIndex(post5.paragraphs.size + 1) // last item
        composeTestRule.waitUntilExactlyOneExists(hasText("Finished"), 5000L)

        composeTestRule.onNodeWithText("Back to top", useUnmergedTree = true).performClick()
        composeTestRule.waitUntilExactlyOneExists(hasText("4 min left"), 5000L)
        composeTestRule.waitUntil(5000L) {
            composeTestRule.onAllNodes(hasText("Back to top"), useUnmergedTree = true).fetchSemanticsNodes().isEmpty()
        }
    }
}
