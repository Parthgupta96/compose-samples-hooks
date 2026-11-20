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

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasScrollAction
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollToIndex
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.example.jetnews.data.posts.impl.post5
import com.example.jetnews.ui.post.PostScreen
import com.example.jetnews.ui.theme.JetnewsTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PostScreenTests {

    @get:Rule
    val composeTestRule = createComposeRule()

    /**
     * Checks the reading progress label and the "Back to top" button through a full read and back.
     */
    @Test
    fun readToEnd_thenBackToTop() {
        composeTestRule.setContent {
            JetnewsTheme {
                PostScreen(post = post5, isExpandedScreen = false, onBack = {}, isFavorite = false, onToggleFavorite = {})
            }
        }

        // At the top: full read time, no button
        composeTestRule.onNodeWithText("4 min left").assertIsDisplayed()
        composeTestRule.onNodeWithText("Back to top").assertDoesNotExist()

        // At the end: finished, button shown (header + metadata + paragraphs)
        composeTestRule.onNode(hasScrollAction()).performScrollToIndex(post5.paragraphs.size + 1)
        composeTestRule.onNodeWithText("Finished").assertIsDisplayed()

        // Back at the top: full read time again, button gone
        composeTestRule.onNodeWithText("Back to top").performClick()
        composeTestRule.waitUntil(5_000) {
            composeTestRule.onAllNodesWithText("4 min left").fetchSemanticsNodes().isNotEmpty() &&
                composeTestRule.onAllNodesWithText("Back to top").fetchSemanticsNodes().isEmpty()
        }
    }
}
