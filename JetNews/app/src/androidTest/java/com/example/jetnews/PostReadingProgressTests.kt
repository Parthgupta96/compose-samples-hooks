/*
 * Copyright 2020 The Android Open Source Project
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
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasScrollToIndexAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
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
class PostReadingProgressTests {

    @get:Rule
    val composeTestRule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun readingProgress_countsDownAndBackToTopResets() {
        composeTestRule.setContent {
            JetnewsTheme { PostScreen(post5, false, {}, false, {}) }
        }
        val backToTop = composeTestRule.activity.getString(R.string.post_back_to_top)

        composeTestRule.onNodeWithText("4 min left").assertIsDisplayed()
        composeTestRule.onNodeWithText(backToTop, useUnmergedTree = true).assertDoesNotExist()

        composeTestRule.onNode(hasScrollToIndexAction()).performScrollToIndex(post5.paragraphs.size + 1)
        composeTestRule.onNodeWithText(composeTestRule.activity.getString(R.string.post_finished)).assertIsDisplayed()

        composeTestRule.onNodeWithText(backToTop, useUnmergedTree = true).performClick()
        composeTestRule.waitUntil(5_000) {
            composeTestRule.onAllNodes(hasText("4 min left")).fetchSemanticsNodes().isNotEmpty()
        }
        composeTestRule.onNodeWithText(backToTop, useUnmergedTree = true).assertDoesNotExist()
    }
}
