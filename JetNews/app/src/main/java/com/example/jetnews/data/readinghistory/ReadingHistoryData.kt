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

import com.example.jetnews.data.posts.impl.post1
import com.example.jetnews.data.posts.impl.post2
import com.example.jetnews.data.posts.impl.post3
import com.example.jetnews.data.posts.impl.post4
import com.example.jetnews.data.posts.impl.post5
import com.example.jetnews.data.posts.impl.post6
import com.example.jetnews.data.posts.impl.posts
import com.example.jetnews.model.ReadingHistoryEntry
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

private val sourcePosts = listOf(post1, post2, post3, post4, post5, post6) + posts.allPosts

// Cycled across entries so both Finished (100) and In progress (< 100, including 99) are populated.
private val percentsRead = listOf(100, 45, 100, 82, 12, 100, 67, 99, 100, 30, 5, 100, 58)

/**
 * About 30 locally generated reading history entries, most recently read first.
 */
val readingHistory: List<ReadingHistoryEntry> = run {
    val dateFormat = SimpleDateFormat("MMMM dd", Locale.getDefault())
    val calendar = Calendar.getInstance().apply { set(2026, Calendar.NOVEMBER, 18) }
    List(30) { index ->
        val post = sourcePosts[index % sourcePosts.size]
        val percentRead = percentsRead[index % percentsRead.size]
        val entry = ReadingHistoryEntry(
            id = "history-$index",
            post = post,
            dateRead = dateFormat.format(calendar.time),
            minutesSpent = (post.metadata.readTimeMinutes * percentRead / 100 + index % 3).coerceAtLeast(1),
            percentRead = percentRead,
        )
        // Step back 0-2 days between entries so some days have several reads.
        calendar.add(Calendar.DAY_OF_MONTH, -(index % 3))
        entry
    }
}
