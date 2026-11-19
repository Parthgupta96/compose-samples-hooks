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

package com.example.jetlagged.ui.util

import android.content.pm.ApplicationInfo
import android.util.Log
import androidx.compose.ui.Modifier
import androidx.compose.ui.node.CompositionLocalConsumerModifierNode
import androidx.compose.ui.node.ModifierNodeElement
import androidx.compose.ui.node.currentValueOf
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private const val TRACKER_TAG = "RecomposeTracker"
private const val RESET_AFTER_MILLIS = 3_000L

/**
 * Logs when the composable that uses this modifier recomposes, for the kit's device check.
 *
 * Logcat tag `RecomposeTracker`: "Composable <tag> attached" when the node first appears, then
 * "Composable <tag> count=<n>" on each recomposition. The count resets after 3 s without one.
 * Does nothing in a build that is not debuggable. Based on the public recompose highlighter snippet,
 * without the border drawing.
 */
fun Modifier.recomposeHighlighter(tag: String): Modifier = this then RecomposeHighlighterElement(tag)

private class RecomposeHighlighterElement(private val tag: String) : ModifierNodeElement<RecomposeHighlighterNode>() {
    override fun create() = RecomposeHighlighterNode(tag)

    override fun update(node: RecomposeHighlighterNode) {
        node.tag = tag
        node.onRecomposed()
    }

    // Identity equality: each recomposition creates a new element, so update() runs every time.
    override fun equals(other: Any?): Boolean = other === this

    override fun hashCode(): Int = System.identityHashCode(this)
}

private class RecomposeHighlighterNode(var tag: String) :
    Modifier.Node(),
    CompositionLocalConsumerModifierNode {
    private var enabled = false
    private var count = 0
    private var resetJob: Job? = null

    override fun onAttach() {
        val flags = currentValueOf(LocalContext).applicationInfo.flags
        enabled = (flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0
        if (enabled) Log.d(TRACKER_TAG, "Composable $tag attached")
    }

    fun onRecomposed() {
        if (!enabled || !isAttached) return
        count++
        Log.d(TRACKER_TAG, "Composable $tag count=$count")
        resetJob?.cancel()
        resetJob = coroutineScope.launch {
            delay(RESET_AFTER_MILLIS)
            count = 0
        }
    }
}
