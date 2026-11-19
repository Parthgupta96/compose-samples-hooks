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

package com.example.jetnews.data.history

import com.example.jetnews.data.posts.impl.post1
import com.example.jetnews.data.posts.impl.post2
import com.example.jetnews.data.posts.impl.post3
import com.example.jetnews.data.posts.impl.post4
import com.example.jetnews.data.posts.impl.post5
import com.example.jetnews.data.posts.impl.post6
import com.example.jetnews.data.posts.impl.posts
import com.example.jetnews.model.Post

data class ReadingHistoryEntry(val id: Int, val post: Post, val dateRead: String, val minutesSpent: Int, val percentRead: Int)

private val percents = listOf(
    100, 72, 100, 35, 100, 88, 12, 100, 54, 100,
    99, 100, 41, 100, 67, 5, 100, 80, 100, 23,
    100, 93, 100, 60, 18, 100, 47, 100, 76, 100,
)

private val sourcePosts = listOf(post1, post2, post3, post4, post5, post6) + posts.allPosts

/** About 30 entries built from the sample posts, most recently read first. */
val readingHistoryEntries: List<ReadingHistoryEntry> = percents.mapIndexed { i, percent ->
    val post = sourcePosts[i % sourcePosts.size]
    // ponytail: fixed dates (Nov 18 back to Oct 20), no clock; swap for real timestamps with real data.
    val day = 18 - i
    ReadingHistoryEntry(
        id = i,
        post = post,
        dateRead = if (day >= 1) "Nov $day" else "Oct ${31 + day}",
        minutesSpent = (post.metadata.readTimeMinutes * percent / 100 + i % 5).coerceAtLeast(1),
        percentRead = percent,
    )
}
