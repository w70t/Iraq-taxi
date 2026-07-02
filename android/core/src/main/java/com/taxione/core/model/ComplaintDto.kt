package com.taxione.core.model

import org.json.JSONObject

data class ComplaintDto(
    val id: String,
    val text: String,
    val status: String,  // open | resolved
    val createdAt: Long,
) {
    companion object {
        fun fromJson(json: JSONObject) = ComplaintDto(
            id = json.optString("id"),
            text = json.optString("text"),
            status = json.optString("status", "open"),
            createdAt = json.optLong("created_at"),
        )
    }
}
