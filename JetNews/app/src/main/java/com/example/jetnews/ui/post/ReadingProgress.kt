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

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.foundation.background
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
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.example.jetnews.R
import com.example.jetnews.utils.isScrolledPastFirstScreen
import com.example.jetnews.utils.scrollFraction
import kotlin.math.ceil

/**
 * Thin progress bar with the reading time left, for an article shown in [state].
 *
 * @param state (state) the [LazyListState] of the article
 * @param readTimeMinutes (state) the article's full read time
 * @param modifier modifier for the root element
 */
@Composable
internal fun ReadingProgress(state: LazyListState, readTimeMinutes: Int, modifier: Modifier = Modifier) {
    val progress by remember(state) { derivedStateOf { state.scrollFraction() } }
    val minutesLeft by remember(state, readTimeMinutes) {
        derivedStateOf { readingMinutesLeft(readTimeMinutes, progress) }
    }
    Column(modifier.background(MaterialTheme.colorScheme.surface)) {
        // The lambda defers the read to drawing, so scrolling redraws the bar without recomposing.
        LinearProgressIndicator(progress = { progress }, modifier = Modifier.fillMaxWidth())
        Text(
            text = if (minutesLeft == 0) {
                stringResource(R.string.post_reading_finished)
            } else {
                stringResource(R.string.post_min_left, minutesLeft)
            },
            style = MaterialTheme.typography.labelMedium,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
        )
    }
}

/**
 * Whole minutes left to read after [progress] (0 to 1) of an article, rounded up. 0 only at the end.
 */
internal fun readingMinutesLeft(readTimeMinutes: Int, progress: Float): Int = ceil(readTimeMinutes * (1 - progress)).toInt()

/**
 * "Back to top" button, shown once [state] is scrolled past its first screen.
 *
 * @param state (state) the [LazyListState] of the article
 * @param onClick (event) request a scroll back to the top
 */
@Composable
internal fun BackToTopButton(state: LazyListState, onClick: () -> Unit) {
    val visible by remember(state) { derivedStateOf { state.isScrolledPastFirstScreen() } }
    AnimatedVisibility(visible = visible, enter = fadeIn() + scaleIn(), exit = fadeOut() + scaleOut()) {
        ExtendedFloatingActionButton(
            text = { Text(stringResource(R.string.post_back_to_top)) },
            icon = { Icon(painterResource(R.drawable.ic_arrow_upward), contentDescription = null) },
            onClick = onClick,
        )
    }
}
