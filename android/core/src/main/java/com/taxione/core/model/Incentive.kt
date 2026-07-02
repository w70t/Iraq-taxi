package com.taxione.core.model

import org.json.JSONObject

data class IncentiveStep(val trips: Int, val bonus: Int)

data class IncentivePlan(
    val id: String,
    val title: String,
    val description: String,
    val secondsRemaining: Long,
    val steps: List<IncentiveStep>,
) {
    companion object {
        fun fromJson(json: JSONObject): IncentivePlan {
            val stepsJson = json.optJSONArray("steps")
            val steps = if (stepsJson == null) emptyList() else (0 until stepsJson.length()).map {
                val step = stepsJson.getJSONObject(it)
                IncentiveStep(trips = step.optInt("trips"), bonus = step.optInt("bonus"))
            }
            return IncentivePlan(
                id = json.optString("id"),
                title = json.optString("title"),
                description = json.optString("description"),
                secondsRemaining = json.optLong("seconds_remaining"),
                steps = steps,
            )
        }
    }
}
