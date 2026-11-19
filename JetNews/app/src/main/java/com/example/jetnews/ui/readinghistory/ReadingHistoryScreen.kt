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
import androidx.compose.animation.core.Animatable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
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
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import androidx.navigation3.runtime.EntryProviderScope
import androidx.navigation3.runtime.NavKey
import com.example.jetnews.R
import com.example.jetnews.data.readinghistory.readingHistory
import com.example.jetnews.deeplink.util.DeepLinkPattern
import com.example.jetnews.model.ReadingHistoryEntry
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
    Finished(R.string.reading_history_filter_finished, { it.isFinished }),
    InProgress(R.string.reading_history_filter_in_progress, { !it.isFinished }),
}

/**
 * Displays past reads in [entries], filterable by [ReadingHistoryFilter].
 *
 * @param entries (state) reading history, most recently read first
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
    val filteredEntries = remember(entries, filter) { entries.filter(filter.matches) }

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
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                ReadingHistoryFilter.entries.forEach { option ->
                    FilterChip(
                        selected = filter == option,
                        onClick = { filter = option },
                        label = { Text(stringResource(option.labelResId)) },
                    )
                }
            }
            if (filteredEntries.isEmpty()) {
                Box(Modifier.fillMaxSize().padding(16.dp), contentAlignment = Alignment.Center) {
                    Text(
                        text = stringResource(R.string.reading_history_empty),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            } else {
                LazyColumn(Modifier.fillMaxSize()) {
                    items(filteredEntries, key = { it.id }) { entry ->
                        ReadingHistoryItem(entry)
                        HorizontalDivider(Modifier.padding(horizontal = 16.dp))
                    }
                }
            }
        }
    }
}

@Composable
private fun ReadingHistoryItem(entry: ReadingHistoryEntry) {
    val post = entry.post
    Column(Modifier.fillMaxWidth().padding(16.dp)) {
        Text(
            text = post.title,
            style = MaterialTheme.typography.titleMedium,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
        Text(
            text = listOfNotNull(post.metadata.author.name, post.publication?.name).joinToString(" · "),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = "${entry.dateRead} · ${stringResource(R.string.reading_history_minutes_spent, entry.minutesSpent)}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(Modifier.padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            ReadingProgressBar(entry.percentRead / 100f, Modifier.weight(1f))
            Text(
                text = stringResource(R.string.reading_history_percent_read, entry.percentRead),
                style = MaterialTheme.typography.labelMedium,
                modifier = Modifier.padding(start = 8.dp).width(40.dp),
            )
        }
    }
}

/**
 * Animates from 0 to [progress] the first time this item is composed. Saveable state survives the
 * item scrolling off screen, so it doesn't replay on every scroll.
 */
@Composable
private fun ReadingProgressBar(progress: Float, modifier: Modifier = Modifier) {
    var hasAnimated by rememberSaveable { mutableStateOf(false) }
    val animatedProgress = remember { Animatable(if (hasAnimated) progress else 0f) }
    LaunchedEffect(progress) {
        animatedProgress.animateTo(progress)
        hasAnimated = true
    }
    LinearProgressIndicator(progress = { animatedProgress.value }, modifier = modifier)
}

@Preview("Reading history screen")
@Preview("Reading history screen (dark)", uiMode = UI_MODE_NIGHT_YES)
@Composable
fun PreviewReadingHistoryScreen() {
    JetnewsTheme {
        ReadingHistoryScreen(entries = readingHistory, isExpandedScreen = false, openDrawer = {})
    }
}
