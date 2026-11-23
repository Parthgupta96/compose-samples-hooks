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

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.example.jetnews.R
import kotlin.math.ceil

/**
 * How far through the list the user has scrolled, from 0 (top) to 1 (end).
 *
 * Lazy items have different heights, so this counts items scrolled past plus the fraction of the
 * first visible one, against the items that have to scroll off before the end is reached.
 */
internal fun LazyListState.readingProgress(): Float {
    val info = layoutInfo
    if (info.totalItemsCount == 0) return 0f
    if (!canScrollForward) return 1f
    val first = info.visibleItemsInfo.firstOrNull() ?: return 0f
    val scrolled = firstVisibleItemIndex + firstVisibleItemScrollOffset / first.size.coerceAtLeast(1).toFloat()
    val scrollable = (info.totalItemsCount - info.visibleItemsInfo.size).coerceAtLeast(1)
    return (scrolled / scrollable).coerceIn(0f, 1f)
}

/**
 * True once the user has scrolled further than one viewport height.
 *
 * Items above the viewport aren't measured, so their height is estimated from the visible ones.
 */
internal fun LazyListState.isPastFirstScreen(): Boolean {
    val info = layoutInfo
    val visible = info.visibleItemsInfo
    if (visible.isEmpty()) return false
    val averageItemSize = visible.sumOf { it.size } / visible.size
    return firstVisibleItemIndex * averageItemSize + firstVisibleItemScrollOffset > info.viewportSize.height
}

/** Whole minutes left to read, rounded up. 0 means finished. */
internal fun minutesLeft(readTimeMinutes: Int, progress: Float): Int = ceil(readTimeMinutes * (1f - progress)).toInt().coerceAtLeast(0)

/**
 * Thin progress bar with an "N min left" label under it.
 *
 * @param progress (state) reading progress from 0 to 1, read during drawing only
 * @param minutesLeft (state) whole minutes left; 0 shows "Finished"
 */
@Composable
internal fun ReadingProgress(progress: () -> Float, minutesLeft: Int, modifier: Modifier = Modifier) {
    Column(modifier) {
        LinearProgressIndicator(progress = progress, modifier = Modifier.fillMaxWidth())
        Text(
            text = if (minutesLeft == 0) {
                stringResource(R.string.post_finished)
            } else {
                pluralStringResource(R.plurals.post_minutes_left, minutesLeft, minutesLeft)
            },
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
        )
    }
}

/** Room left under the article for the "Back to top" button: its 56dp height plus the 16dp FAB margin. */
internal val BackToTopClearance = 72.dp

@Composable
internal fun BackToTopButton(onClick: () -> Unit, modifier: Modifier = Modifier) {
    val label = stringResource(R.string.post_back_to_top)
    ExtendedFloatingActionButton(
        onClick = onClick,
        icon = { Icon(painterResource(R.drawable.ic_arrow_upward), contentDescription = null) },
        text = { Text(label) },
        // The FAB's label isn't exposed to accessibility services, so set it on the button
        modifier = modifier.semantics { contentDescription = label },
    )
}
