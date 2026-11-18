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

package com.example.jetlagged.sleep

import androidx.annotation.StringRes
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.jetlagged.BasicInformationalCard
import com.example.jetlagged.R
import com.example.jetlagged.backgrounds.movingStripesBackground
import com.example.jetlagged.data.sleepHistoryData
import com.example.jetlagged.ui.theme.HeadingStyle
import com.example.jetlagged.ui.theme.JetLaggedTheme
import com.example.jetlagged.ui.theme.LegendHeadingStyle
import com.example.jetlagged.ui.theme.SmallHeadingStyle
import java.time.format.DateTimeFormatter

@Composable
fun SleepHistoryScreen(modifier: Modifier = Modifier, history: SleepGraphData = sleepHistoryData, onDrawerClick: () -> Unit = {}) {
    var filter by rememberSaveable { mutableStateOf(SleepHistoryFilter.All) }
    val nights = remember(history, filter) {
        history.sleepDayData.filter { filter.matches(it.sleepScore) }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        JetLaggedHeader(
            modifier = Modifier
                .fillMaxWidth()
                .movingStripesBackground(
                    stripeColor = JetLaggedTheme.extraColors.header,
                    backgroundColor = MaterialTheme.colorScheme.background,
                ),
            title = stringResource(R.string.sleep_history_heading),
            onDrawerClick = onDrawerClick,
        )
        Row(
            modifier = Modifier.padding(horizontal = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            SleepHistoryFilter.entries.forEach {
                FilterChip(
                    selected = filter == it,
                    onClick = { filter = it },
                    label = { Text(stringResource(it.label)) },
                )
            }
        }
        if (nights.isEmpty()) {
            Text(
                stringResource(R.string.sleep_history_empty),
                modifier = Modifier.padding(16.dp),
                style = SmallHeadingStyle,
            )
        }
        LazyColumn(
            contentPadding = WindowInsets.safeDrawing
                .only(WindowInsetsSides.Bottom + WindowInsetsSides.Horizontal)
                .asPaddingValues(),
        ) {
            items(nights, key = { it.startDate }) {
                SleepHistoryRow(night = it, modifier = Modifier.fillMaxWidth())
            }
        }
    }
}

@Composable
private fun SleepHistoryRow(night: SleepDayData, modifier: Modifier = Modifier) {
    BasicInformationalCard(
        borderColor = JetLaggedTheme.extraColors.sleep,
        modifier = modifier,
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(night.startDate.format(dateFormatter), style = SmallHeadingStyle)
                    Text(formatDuration(night.totalSleep.toMinutes()), style = HeadingStyle)
                }
                val scoreDescription = stringResource(R.string.sleep_history_score, night.sleepScore)
                Text(
                    night.sleepScore.toString(),
                    modifier = Modifier.semantics { contentDescription = scoreDescription },
                    style = HeadingStyle,
                )
            }
            ScoreBar(score = night.sleepScore, modifier = Modifier.fillMaxWidth())
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                SleepType.entries.forEach {
                    StageTime(sleepType = it, minutes = night.timeInStage.getValue(it).toMinutes())
                }
            }
        }
    }
}

@Composable
private fun ScoreBar(score: Int, modifier: Modifier = Modifier) {
    // Saved per row, so the bar fills only the first time the row is shown, not on every scroll back.
    var hasAnimated by rememberSaveable { mutableStateOf(false) }
    val fraction = remember { Animatable(if (hasAnimated) score / 100f else 0f) }
    LaunchedEffect(score) {
        fraction.animateTo(score / 100f, tween(durationMillis = 800))
        hasAnimated = true
    }
    val trackColor = MaterialTheme.colorScheme.surfaceVariant
    val barColor = JetLaggedTheme.extraColors.sleepChartPrimary
    Box(
        modifier = modifier
            .height(8.dp)
            .drawBehind {
                val radius = CornerRadius(size.height / 2)
                drawRoundRect(trackColor, cornerRadius = radius)
                drawRoundRect(
                    barColor,
                    size = Size(size.width * fraction.value, size.height),
                    cornerRadius = radius,
                )
            },
    )
}

@Composable
private fun StageTime(sleepType: SleepType, minutes: Long) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(10.dp)
                .clip(CircleShape)
                .background(colorForSleepType(sleepType)),
        )
        Text(
            "${stringResource(sleepType.title)} ${formatDuration(minutes)}",
            style = LegendHeadingStyle,
            modifier = Modifier.padding(start = 4.dp),
        )
    }
}

@Composable
private fun formatDuration(minutes: Long): String = stringResource(R.string.sleep_history_duration, minutes / 60, minutes % 60)

private enum class SleepHistoryFilter(@StringRes val label: Int, val matches: (score: Int) -> Boolean) {
    All(R.string.sleep_history_filter_all, { true }),
    Good(R.string.sleep_history_filter_good, { it >= GOOD_SLEEP_SCORE }),
    Poor(R.string.sleep_history_filter_poor, { it < GOOD_SLEEP_SCORE }),
}

private const val GOOD_SLEEP_SCORE = 70
private val dateFormatter = DateTimeFormatter.ofPattern("EEE, MMM d")

@Preview
@Composable
private fun SleepHistoryScreenPreview() {
    JetLaggedTheme {
        SleepHistoryScreen()
    }
}
