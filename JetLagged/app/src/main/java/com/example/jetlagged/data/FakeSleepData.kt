/*
 * Copyright 2022 The Android Open Source Project
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

package com.example.jetlagged.data

import com.example.jetlagged.sleep.SleepDayData
import com.example.jetlagged.sleep.SleepGraphData
import com.example.jetlagged.sleep.SleepPeriod
import com.example.jetlagged.sleep.SleepType
import java.time.LocalDate
import java.time.LocalDateTime
import kotlin.random.Random

// In the real world, you should get this data from a backend.
val sleepData = SleepGraphData(
    listOf(
        SleepDayData(
            LocalDateTime.now().minusDays(7),
            listOf(
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(21)
                        .withMinute(8),
                    endTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(21)
                        .withMinute(40),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(21)
                        .withMinute(40),
                    endTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(22)
                        .withMinute(20),
                    type = SleepType.Light,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(22)
                        .withMinute(20),
                    endTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(22)
                        .withMinute(50),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(22)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(23)
                        .withMinute(30),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(7)
                        .withHour(23)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(1)
                        .withMinute(10),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(1)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(2)
                        .withMinute(30),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(2)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(4)
                        .withMinute(10),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(4)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(5)
                        .withMinute(30),
                    type = SleepType.Awake,
                ),
            ),
            sleepScore = 90,
        ),
        SleepDayData(
            LocalDateTime.now().minusDays(6),
            listOf(
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(22)
                        .withMinute(38),
                    endTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(22)
                        .withMinute(50),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(22)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(23)
                        .withMinute(30),
                    type = SleepType.Light,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(23)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(23)
                        .withMinute(55),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(6)
                        .withHour(23)
                        .withMinute(55),
                    endTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(2)
                        .withMinute(40),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(2)
                        .withMinute(40),
                    endTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(2)
                        .withMinute(50),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(2)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(4)
                        .withMinute(12),
                    type = SleepType.Deep,
                ),
            ),
            sleepScore = 70,
        ),
        SleepDayData(
            LocalDateTime.now().minusDays(5),
            listOf(
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(22)
                        .withMinute(8),
                    endTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(22)
                        .withMinute(40),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(22)
                        .withMinute(40),
                    endTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(22)
                        .withMinute(50),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(22)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(22)
                        .withMinute(55),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(22)
                        .withMinute(55),
                    endTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(23)
                        .withMinute(30),
                    type = SleepType.Light,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(5)
                        .withHour(23)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(1)
                        .withMinute(10),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(1)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(2)
                        .withMinute(30),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(2)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(3)
                        .withMinute(5),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(3)
                        .withMinute(5),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(4)
                        .withMinute(50),
                    type = SleepType.Light,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(4)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(6)
                        .withMinute(30),
                    type = SleepType.REM,
                ),
            ),
            sleepScore = 60,
        ),
        SleepDayData(
            LocalDateTime.now().minusDays(4),
            listOf(
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(20)
                        .withMinute(20),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(22)
                        .withMinute(40),
                    type = SleepType.Light,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(22)
                        .withMinute(40),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(22)
                        .withMinute(50),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(22)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(23)
                        .withMinute(55),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(4)
                        .withHour(23)
                        .withMinute(55),
                    endTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(1)
                        .withMinute(33),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(1)
                        .withMinute(33),
                    endTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(2)
                        .withMinute(30),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(2)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(3)
                        .withMinute(45),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(3)
                        .withMinute(45),
                    endTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(7)
                        .withMinute(15),
                    type = SleepType.Light,
                ),
            ),
            sleepScore = 90,
        ),
        SleepDayData(
            LocalDateTime.now().minusDays(3),
            listOf(
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(22)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(23)
                        .withMinute(30),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(3)
                        .withHour(23)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(0)
                        .withMinute(10),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(0)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(1)
                        .withMinute(10),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(1)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(2)
                        .withMinute(30),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(2)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(4)
                        .withMinute(30),
                    type = SleepType.Light,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(4)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(4)
                        .withMinute(45),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(4)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(4)
                        .withMinute(45),
                    type = SleepType.REM,
                ),
            ),
            sleepScore = 40,
        ),
        SleepDayData(
            LocalDateTime.now().minusDays(2),
            listOf(
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(20)
                        .withMinute(40),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(21)
                        .withMinute(40),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(21)
                        .withMinute(40),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(22)
                        .withMinute(20),
                    type = SleepType.Light,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(22)
                        .withMinute(20),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(22)
                        .withMinute(50),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(22)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(23)
                        .withMinute(30),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(2)
                        .withHour(23)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(1)
                        .withMinute(10),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(1)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(2)
                        .withMinute(30),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(2)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(4)
                        .withMinute(10),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(4)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(5)
                        .withMinute(30),
                    type = SleepType.Awake,
                ),
            ),
            sleepScore = 82,
        ),
        SleepDayData(
            LocalDateTime.now().minusDays(1),
            listOf(
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(22)
                        .withMinute(8),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(22)
                        .withMinute(40),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(22)
                        .withMinute(40),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(22)
                        .withMinute(50),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(22)
                        .withMinute(50),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(22)
                        .withMinute(55),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(22)
                        .withMinute(55),
                    endTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(23)
                        .withMinute(30),
                    type = SleepType.REM,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .minusDays(1)
                        .withHour(23)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .withHour(1)
                        .withMinute(10),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .withHour(1)
                        .withMinute(10),
                    endTime = LocalDateTime.now()
                        .withHour(2)
                        .withMinute(30),
                    type = SleepType.Awake,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .withHour(2)
                        .withMinute(30),
                    endTime = LocalDateTime.now()
                        .withHour(3)
                        .withMinute(5),
                    type = SleepType.Deep,
                ),
                SleepPeriod(
                    startTime = LocalDateTime.now()
                        .withHour(3)
                        .withMinute(5),
                    endTime = LocalDateTime.now()
                        .withHour(4)
                        .withMinute(50),
                    type = SleepType.Light,
                ),
            ),
            sleepScore = 70,
        ),
    ),
)

// About a month of nights for the sleep history screen, most recent first.
// A fixed seed keeps the list stable between launches.
val sleepHistoryData: List<SleepDayData> = generateSleepHistory(nights = 30, random = Random(seed = 7))

private fun generateSleepHistory(nights: Int, random: Random): List<SleepDayData> {
    val today = LocalDate.now()
    return (1..nights).map { daysAgo ->
        val bedtime = today.minusDays(daysAgo.toLong()).atTime(21, 30).plusMinutes(random.nextLong(0, 120))
        val periods = mutableListOf<SleepPeriod>()
        fun add(type: SleepType, minutes: Long) {
            val start = periods.lastOrNull()?.endTime ?: bedtime
            periods += SleepPeriod(start, start.plusMinutes(minutes), type)
        }
        add(SleepType.Awake, random.nextLong(5, 30))
        // Four to six sleep cycles of roughly 45 to 120 minutes each, sometimes broken by waking up.
        repeat(random.nextInt(4, 7)) {
            add(SleepType.Light, random.nextLong(25, 50))
            add(SleepType.Deep, random.nextLong(10, 40))
            add(SleepType.REM, random.nextLong(10, 30))
            if (random.nextInt(4) == 0) add(SleepType.Awake, random.nextLong(5, 25))
        }
        val minutesAsleep = periods.filter { it.type != SleepType.Awake }.sumOf { it.duration.toMinutes() }
        // Longer nights score higher, with some noise so the score is not just a function of duration.
        val score = (minutesAsleep / 480.0 * 85 + random.nextInt(-8, 9)).toInt().coerceIn(20, 99)
        SleepDayData(bedtime, periods, score)
    }
}
