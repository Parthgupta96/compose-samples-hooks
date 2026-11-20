/*
 * Copyright 2021 The Android Open Source Project
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

package com.example.jetnews.utils

import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.runtime.derivedStateOf

val LazyListState.isScrolled: Boolean
    get() = derivedStateOf { firstVisibleItemIndex > 0 || firstVisibleItemScrollOffset > 0 }.value

// ponytail: items above the first visible one are estimated at the visible items' average size, so
// the bar can drift a little past items of very different heights. Measure every item if that shows.
private val LazyListState.averageItemSize: Float
    get() = layoutInfo.visibleItemsInfo.let { items -> items.sumOf { it.size }.toFloat() / items.size } +
        layoutInfo.mainAxisItemSpacing

private val LazyListState.estimatedScrollOffset: Float
    get() = firstVisibleItemIndex * averageItemSize + firstVisibleItemScrollOffset

/** How far the list is scrolled: 0 at the top, 1 only once it cannot scroll further. */
fun LazyListState.scrollFraction(): Float {
    val info = layoutInfo
    if (info.visibleItemsInfo.isEmpty()) return 0f
    if (!canScrollForward) return 1f
    val scrollRange = info.totalItemsCount * averageItemSize + info.beforeContentPadding + info.afterContentPadding -
        info.viewportSize.height
    // Held below 1 until the real end, so an estimate that runs short never reports the end early.
    return (estimatedScrollOffset / scrollRange.coerceAtLeast(1f)).coerceIn(0f, 0.99f)
}

/** Whether the list is scrolled more than one viewport height past its top. */
fun LazyListState.isScrolledPastFirstScreen(): Boolean =
    layoutInfo.visibleItemsInfo.isNotEmpty() && estimatedScrollOffset > layoutInfo.viewportSize.height
