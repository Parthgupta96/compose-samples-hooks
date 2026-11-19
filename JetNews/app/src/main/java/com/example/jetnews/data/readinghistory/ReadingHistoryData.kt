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

package com.example.jetnews.data.readinghistory

import com.example.jetnews.data.posts.impl.posts
import com.example.jetnews.model.Post
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

data class ReadingHistoryEntry(val id: String, val post: Post, val dateRead: String, val minutesSpent: Int, val percentRead: Int)

// One entry per value, most recent first. Mixes finished (100) and in-progress reads, including the 99 / 0 edges.
private val percentsRead = listOf(
    100, 42, 100, 75, 8, 100, 63, 0, 100, 27,
    91, 100, 54, 100, 15, 88, 100, 36, 99, 70,
    100, 3, 49, 100, 82, 21, 100, 59, 100, 95,
)

/**
 * Locally generated reading history, built by cycling through the sample posts in [posts].
 */
val readingHistory: List<ReadingHistoryEntry> = percentsRead.mapIndexed { index, percent ->
    val post = posts.allPosts[index % posts.allPosts.size]
    ReadingHistoryEntry(
        id = "history-$index",
        post = post,
        dateRead = formatDaysAgo(index + index / 3),
        minutesSpent = (post.metadata.readTimeMinutes * percent / 100 + index % 4).coerceAtLeast(1),
        percentRead = percent,
    )
}

// java.time needs API 26 without desugaring; minSdk is 24.
private fun formatDaysAgo(daysAgo: Int): String {
    val calendar = Calendar.getInstance().apply { add(Calendar.DAY_OF_YEAR, -daysAgo) }
    return SimpleDateFormat("MMM d", Locale.getDefault()).format(calendar.time)
}
