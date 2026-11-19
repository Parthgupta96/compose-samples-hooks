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

package com.example.jetnews.ui.readinghistory

import android.content.res.Configuration.UI_MODE_NIGHT_YES
import androidx.annotation.StringRes
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
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
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Devices
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import androidx.navigation3.runtime.EntryProviderScope
import androidx.navigation3.runtime.NavKey
import com.example.jetnews.R
import com.example.jetnews.data.readinghistory.ReadingHistoryEntry
import com.example.jetnews.data.readinghistory.readingHistory
import com.example.jetnews.deeplink.util.DeepLinkPattern
import com.example.jetnews.ui.theme.JetnewsTheme
import kotlinx.serialization.Serializable

@Serializable
data object ReadingHistoryKey : NavKey

val ReadingHistoryDeepLinkPattern = DeepLinkPattern(
    ReadingHistoryKey.serializer(),
    uriPattern = "https://developer.android.com/jetnews/reading-history".toUri(),
)

fun EntryProviderScope<NavKey>.readingHistoryEntry(isExpandedScreen: () -> Boolean, openDrawer: () -> Unit) {
    entry<ReadingHistoryKey> {
        ReadingHistoryScreen(
            entries = readingHistory,
            isExpandedScreen = isExpandedScreen(),
            openDrawer = openDrawer,
        )
    }
}

enum class ReadingHistoryFilter(@StringRes val labelResId: Int, val matches: (ReadingHistoryEntry) -> Boolean) {
    All(R.string.reading_history_filter_all, { true }),
    Finished(R.string.reading_history_filter_finished, { it.percentRead >= 100 }),
    InProgress(R.string.reading_history_filter_in_progress, { it.percentRead < 100 }),
}

/**
 * Displays the user's reading history, filterable by [ReadingHistoryFilter].
 *
 * @param entries (state) reading history entries, most recently read first
 * @param isExpandedScreen (state) true if the screen is expanded
 * @param openDrawer (event) request opening the app drawer
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReadingHistoryScreen(
    entries: List<ReadingHistoryEntry>,
    isExpandedScreen: Boolean,
    openDrawer: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var filter by rememberSaveable { mutableStateOf(ReadingHistoryFilter.All) }
    val visibleEntries = remember(entries, filter) { entries.filter(filter.matches) }

    Scaffold(
        modifier = modifier,
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.reading_history_title),
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.primary,
                    )
                },
                navigationIcon = {
                    if (!isExpandedScreen) {
                        IconButton(onClick = openDrawer) {
                            Icon(
                                painter = painterResource(R.drawable.ic_jetnews_logo),
                                contentDescription = stringResource(R.string.cd_open_navigation_drawer),
                            )
                        }
                    }
                },
            )
        },
    ) { innerPadding ->
        Column(Modifier.padding(innerPadding)) {
            Row(
                modifier = Modifier.padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                ReadingHistoryFilter.entries.forEach { option ->
                    FilterChip(
                        selected = option == filter,
                        onClick = { filter = option },
                        label = { Text(stringResource(option.labelResId)) },
                    )
                }
            }
            if (visibleEntries.isEmpty()) {
                Text(
                    text = stringResource(R.string.reading_history_empty),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(32.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    textAlign = TextAlign.Center,
                )
            } else {
                LazyColumn(Modifier.weight(1f)) {
                    items(visibleEntries, key = { it.id }) { entry ->
                        ReadingHistoryRow(entry)
                        HorizontalDivider(
                            modifier = Modifier.padding(horizontal = 16.dp),
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.1f),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun ReadingHistoryRow(entry: ReadingHistoryEntry, modifier: Modifier = Modifier) {
    // Saved per item key, so the bar animates only the first time the row appears, not on every scroll back.
    // Previews start revealed because static previews never run effects.
    val inPreview = LocalInspectionMode.current
    var revealed by rememberSaveable { mutableStateOf(inPreview) }
    LaunchedEffect(Unit) { revealed = true }
    val progress by animateFloatAsState(
        targetValue = if (revealed) entry.percentRead / 100f else 0f,
        animationSpec = tween(durationMillis = 800),
        label = "readingProgress",
    )

    Column(modifier.padding(horizontal = 16.dp, vertical = 12.dp)) {
        Text(entry.post.title, style = MaterialTheme.typography.titleMedium)
        Text(
            text = listOfNotNull(entry.post.metadata.author.name, entry.post.publication?.name).joinToString(" · "),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = stringResource(R.string.reading_history_date_and_time, entry.dateRead, entry.minutesSpent),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(
            modifier = Modifier.padding(top = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier.weight(1f),
            )
            Spacer(Modifier.width(12.dp))
            Text(
                text = stringResource(R.string.reading_history_percent, entry.percentRead),
                style = MaterialTheme.typography.labelMedium,
            )
        }
    }
}

@Preview("Reading history screen", "Reading history")
@Preview("Reading history screen (dark)", "Reading history", uiMode = UI_MODE_NIGHT_YES)
@Preview("Reading history screen (big font)", "Reading history", fontScale = 1.5f)
@Composable
private fun PreviewReadingHistoryScreen() {
    JetnewsTheme {
        ReadingHistoryScreen(entries = readingHistory, isExpandedScreen = false, openDrawer = {})
    }
}

@Preview("Reading history screen navrail", "Reading history", device = Devices.PIXEL_C)
@Composable
private fun PreviewReadingHistoryScreenNavRail() {
    JetnewsTheme {
        ReadingHistoryScreen(entries = readingHistory, isExpandedScreen = true, openDrawer = {})
    }
}

@Preview("Reading history screen empty", "Reading history")
@Composable
private fun PreviewReadingHistoryScreenEmpty() {
    JetnewsTheme {
        ReadingHistoryScreen(entries = emptyList(), isExpandedScreen = false, openDrawer = {})
    }
}
