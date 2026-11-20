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

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.State
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.example.jetnews.R
import kotlin.math.ceil

/**
 * How far the article has been read: 0 at the top, 1 at the end.
 *
 * Measured in items: the items scrolled past above the viewport against the items still below it.
 */
fun LazyListState.readingProgress(): Float {
    val visibleItems = layoutInfo.visibleItemsInfo
    if (visibleItems.isEmpty()) return 0f
    if (!canScrollForward) return 1f
    val first = visibleItems.firstOrNull { it.index == firstVisibleItemIndex } ?: visibleItems.first()
    val last = visibleItems.last()
    val above = firstVisibleItemIndex + firstVisibleItemScrollOffset.toFloat() / first.size.coerceAtLeast(1)
    val contentEnd = layoutInfo.viewportEndOffset - layoutInfo.afterContentPadding
    val hiddenBelow = (last.offset + last.size - contentEnd).coerceIn(0, last.size)
    val below = layoutInfo.totalItemsCount - 1 - last.index + hiddenBelow.toFloat() / last.size.coerceAtLeast(1)
    return if (below <= 0f) 1f else (above / (above + below)).coerceIn(0f, 1f)
}

/** Whole minutes left to read, rounded up. */
fun minutesLeft(readTimeMinutes: Int, progress: Float): Int = ceil(readTimeMinutes * (1f - progress)).toInt()

/**
 * Whether the "Back to top" button shows: after the user scrolls past the first screen, until they are back
 * within half a screen of the top.
 */
@Composable
fun rememberShowBackToTop(state: LazyListState): State<Boolean> {
    val show = remember(state) { mutableStateOf(false) }
    LaunchedEffect(state) {
        // Sizes of the items seen so far, to tell how many pixels have been scrolled past.
        val itemSizes = HashMap<Int, Int>()
        snapshotFlow { Triple(state.layoutInfo, state.firstVisibleItemIndex, state.firstVisibleItemScrollOffset) }
            .collect { (layoutInfo, firstIndex, firstOffset) ->
                layoutInfo.visibleItemsInfo.forEach { itemSizes[it.index] = it.size }
                // Items never laid out (the screen opened part way down) count as the average size.
                val averageSize = itemSizes.values.average().toInt()
                val scrolled = (0 until firstIndex).sumOf { itemSizes[it] ?: averageSize } + firstOffset
                val screen = layoutInfo.viewportSize.height - layoutInfo.beforeContentPadding - layoutInfo.afterContentPadding
                show.value = scrolled > if (show.value) screen / 2 else screen
            }
    }
    return show
}

/**
 * A progress bar with "N min left" under it, or "Finished" at the end of the article.
 *
 * @param progress (state) how far the article has been read, from 0 to 1
 * @param readTimeMinutes (state) read time of the whole article
 * @param containerColor (state) background, so the article does not show through when it scrolls under
 * @param modifier modifier for the root element
 */
@Composable
fun ReadingProgress(progress: () -> Float, readTimeMinutes: Int, containerColor: Color, modifier: Modifier = Modifier) {
    val minutes by remember(progress, readTimeMinutes) {
        derivedStateOf { minutesLeft(readTimeMinutes, progress()) }
    }
    Column(modifier.background(containerColor)) {
        LinearProgressIndicator(progress = progress, modifier = Modifier.fillMaxWidth())
        Text(
            text = if (minutes > 0) {
                stringResource(R.string.post_min_left, minutes)
            } else {
                stringResource(R.string.post_finished)
            },
            style = MaterialTheme.typography.labelMedium,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
        )
    }
}
