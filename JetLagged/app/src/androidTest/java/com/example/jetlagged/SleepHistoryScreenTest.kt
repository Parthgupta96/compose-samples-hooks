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

package com.example.jetlagged

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.example.jetlagged.sleep.SleepDayData
import com.example.jetlagged.sleep.SleepHistoryScreen
import com.example.jetlagged.sleep.SleepPeriod
import com.example.jetlagged.sleep.SleepType
import com.example.jetlagged.ui.theme.JetLaggedTheme
import java.time.LocalDateTime
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class SleepHistoryScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private fun night(daysAgo: Long, score: Int): SleepDayData {
        val start = LocalDateTime.now().minusDays(daysAgo).withHour(22)
        return SleepDayData(start, listOf(SleepPeriod(start, start.plusHours(7), SleepType.Light)), score)
    }

    @Before
    fun setUp() {
        composeTestRule.setContent {
            JetLaggedTheme {
                SleepHistoryScreen(nights = listOf(night(1, 70), night(2, 69)))
            }
        }
    }

    @Test
    fun goodAndPoorSplitAtSeventy() {
        composeTestRule.onNodeWithText("Score 70").assertIsDisplayed()
        composeTestRule.onNodeWithText("Score 69").assertIsDisplayed()

        composeTestRule.onNodeWithText("Good").performClick()
        composeTestRule.onNodeWithText("Score 70").assertIsDisplayed()
        composeTestRule.onNodeWithText("Score 69").assertDoesNotExist()

        composeTestRule.onNodeWithText("Poor").performClick()
        composeTestRule.onNodeWithText("Score 69").assertIsDisplayed()
        composeTestRule.onNodeWithText("Score 70").assertDoesNotExist()
    }
}
