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
import androidx.compose.foundation.layout.ExperimentalLayoutApi
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
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.jetlagged.BasicInformationalCard
import com.example.jetlagged.R
import com.example.jetlagged.data.sleepHistoryData
import com.example.jetlagged.ui.theme.HeadingStyle
import com.example.jetlagged.ui.theme.JetLaggedTheme
import com.example.jetlagged.ui.theme.SmallHeadingStyle
import com.example.jetlagged.ui.theme.TitleBarStyle
import java.time.Duration
import java.time.format.DateTimeFormatter

private const val GOOD_SLEEP_SCORE = 70

enum class SleepHistoryFilter(@StringRes val label: Int, val matches: (SleepDayData) -> Boolean) {
    All(R.string.sleep_history_filter_all, { true }),
    Good(R.string.sleep_history_filter_good, { it.sleepScore >= GOOD_SLEEP_SCORE }),
    Poor(R.string.sleep_history_filter_poor, { it.sleepScore < GOOD_SLEEP_SCORE }),
}

@Composable
fun SleepHistoryScreen(modifier: Modifier = Modifier, nights: List<SleepDayData> = sleepHistoryData, onDrawerClicked: () -> Unit = {}) {
    var filter by rememberSaveable { mutableStateOf(SleepHistoryFilter.All) }
    val visibleNights = remember(nights, filter) { nights.filter(filter.matches) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .windowInsetsPadding(WindowInsets.safeDrawing.only(WindowInsetsSides.Top + WindowInsetsSides.Horizontal)),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onDrawerClicked) {
                Icon(
                    painter = painterResource(id = R.drawable.ic_menu),
                    contentDescription = stringResource(R.string.open_navigation_drawer),
                )
            }
            Text(stringResource(R.string.sleep_history_heading), style = TitleBarStyle)
        }
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
        if (visibleNights.isEmpty()) {
            Text(
                stringResource(R.string.sleep_history_empty),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                textAlign = TextAlign.Center,
            )
        } else {
            LazyColumn(
                modifier = Modifier.padding(horizontal = 8.dp),
                contentPadding = WindowInsets.safeDrawing.only(WindowInsetsSides.Bottom).asPaddingValues(),
            ) {
                items(visibleNights, key = { it.startDate.toLocalDate().toEpochDay() }) { night ->
                    SleepHistoryRow(night)
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun SleepHistoryRow(night: SleepDayData, modifier: Modifier = Modifier) {
    BasicInformationalCard(
        borderColor = JetLaggedTheme.extraColors.sleep,
        modifier = modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(night.startDate.format(dateFormatter), style = SmallHeadingStyle)
                    Text(formatDuration(night.totalTimeAsleep), style = HeadingStyle)
                }
                Text(stringResource(R.string.sleep_history_score, night.sleepScore), style = SmallHeadingStyle)
            }
            SleepScoreBar(night.sleepScore)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                SleepType.entries.forEach { type ->
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(colorForSleepType(type)),
                        )
                        Text(
                            "${stringResource(type.title)} ${formatDuration(night.timeIn(type))}",
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(start = 4.dp),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun SleepScoreBar(score: Int, modifier: Modifier = Modifier) {
    // Saved under the row's key, so scrolling a row back into view doesn't replay the animation.
    var hasAnimated by rememberSaveable { mutableStateOf(false) }
    val skipAnimation = hasAnimated || LocalInspectionMode.current
    val progress = remember { Animatable(if (skipAnimation) 1f else 0f) }
    LaunchedEffect(Unit) {
        progress.animateTo(1f, tween(durationMillis = 800))
        hasAnimated = true
    }
    val fillColor = JetLaggedTheme.extraColors.sleep
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(8.dp)
            .clip(CircleShape)
            .background(fillColor.copy(alpha = 0.2f))
            // Read progress in the draw phase so the animation doesn't recompose the row.
            .drawBehind {
                drawRoundRect(
                    color = fillColor,
                    size = size.copy(width = size.width * score / 100f * progress.value),
                    cornerRadius = CornerRadius(size.height / 2),
                )
            },
    )
}

@Composable
private fun formatDuration(duration: Duration): String =
    stringResource(R.string.sleep_history_duration, duration.toHours(), duration.toMinutes() % 60)

private val dateFormatter = DateTimeFormatter.ofPattern("EEE, MMM d")

@Preview
@Composable
fun SleepHistoryScreenPreview() {
    JetLaggedTheme {
        SleepHistoryScreen()
    }
}
