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

// About a month of nights, most recent first. Seeded so the list is the same on every launch.
val sleepHistoryData = SleepGraphData(
    Random(seed = 30).let { random -> List(30) { generateNight(daysAgo = it + 1L, random = random) } },
)

private fun generateNight(daysAgo: Long, random: Random): SleepDayData {
    val bedtime = LocalDate.now().minusDays(daysAgo).atTime(21, 30).plusMinutes(random.nextLong(0, 120))
    val periods = mutableListOf<SleepPeriod>()
    var cursor = bedtime
    fun add(type: SleepType, minutes: Long) {
        val end = cursor.plusMinutes(minutes)
        periods += SleepPeriod(startTime = cursor, endTime = end, type = type)
        cursor = end
    }

    add(SleepType.Awake, random.nextLong(5, 30))
    // Roughly 90-minute cycles of light, deep and REM sleep, with the odd wake-up.
    repeat(random.nextInt(3, 6)) {
        add(SleepType.Light, random.nextLong(30, 60))
        add(SleepType.Deep, random.nextLong(15, 45))
        add(SleepType.REM, random.nextLong(15, 35))
        if (random.nextInt(4) == 0) add(SleepType.Awake, random.nextLong(5, 25))
    }

    val night = SleepDayData(bedtime, periods, sleepScore = 0)
    // 8 hours asleep scores 100; each 3 minutes awake costs a point.
    val awakeMinutes = night.timeInStage.getValue(SleepType.Awake).toMinutes()
    val score = night.totalSleep.toMinutes() * 100 / FULL_NIGHT_MINUTES - awakeMinutes / 3
    return night.copy(sleepScore = score.toInt().coerceIn(0, 100))
}

private const val FULL_NIGHT_MINUTES = 8 * 60
