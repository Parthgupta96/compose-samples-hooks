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

package com.example.jetnews

import com.example.jetnews.ui.post.minutesLeft
import org.junit.Assert.assertEquals
import org.junit.Test

class ReadingProgressTest {
    @Test
    fun minutesLeft_roundsUpAndFinishesAtEnd() {
        assertEquals(4, minutesLeft(4, 0f))
        assertEquals(3, minutesLeft(4, 0.3f))
        assertEquals(1, minutesLeft(4, 0.99f))
        assertEquals(0, minutesLeft(4, 1f))
        assertEquals(1, minutesLeft(1, 0f))
        assertEquals(0, minutesLeft(1, 1f))
    }
}
