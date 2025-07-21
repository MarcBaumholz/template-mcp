package com.${Company}.${Project}.services

import com.${Company}.${Project}.clients.${Backend}.${FacadeClient}
import com.${Company}.${Project}.models.${ResponseWrapper}
import com.${Company}.${Project}.models.${ResponseItem}
import com.${Company}.${Project}.models.${CreationModel}
import com.${Company}.${Project}.models.${DurationModel}
import com.${Company}.${Project}.models.${DurationUnitEnum}
import com.${Company}.${Project}.models.${StatusEnum}
import com.${Company}.${Project}.models.${TypeEnum}
import io.micronaut.serde.annotation.SerdeImport
import jakarta.inject.Singleton
import java.time.OffsetDateTime

// Alias types: replace with your generated model classes

// Raw entry type alias
// typealias ${EntryType} = ${DetailEntriesType}
// Raw plan type alias
// typealias ${PlanType}  = ${PlanModelType}


/**
 * ${ServiceName}
 *
 * A generic service template for CRUD-like operations:
 * 2) Fetch list of resources
 * 3) Extract single identifier
 * 4) Fetch detailed entries
 * 5) Map to domain models
 */
@SerdeImport(${ResponseWrapper}::class)
@SerdeImport(${ResponseItem}::class)
@SerdeImport(${DurationModel}::class)
@SerdeImport(${StatusEnum}::class)
@SerdeImport(${TypeEnum}::class)
@SerdeImport(${CreationModel}::class)
@Singleton
class ${ServiceName}(
    private val client: ${FacadeClient},
) {

  /**
   * Retrieves and maps a collection of ${PluralResource} for the given identifier.
   */
  suspend fun get${PluralResource}(identifier: String): ${ResponseWrapper} {
    // 2. Fetch list of resources
    val items = client.list${PluralResource}(identifier)?.data
      ?: error("No ${PluralResource} found for identifier: $identifier")

    // 3. Expect exactly one resource and extract its ID
    val resourceId = items.singleOrNull()?.id
      ?: error("Expected exactly one ${SingularResource} record, found: ${'$'}{items.size}")

    // 4. Fetch detailed entries by ID
    val entries = client.get${DetailEntriesType}(resourceId)?.data
      ?: emptyList()

    // 5. Map raw entries to domain models
    val domainList = entries.map { it.to${DomainModel}() }

    return ${ResponseWrapper}(domainList)
  }

  /**
   * Maps a raw entry (${EntryType}) to the domain model (${ResponseItem}).
   */
  private fun ${EntryType}.to${DomainModel}(): ${ResponseItem} =
    ${ResponseItem}(
      field2    = this.${directmatch1}!!,
      field3    = this.${similarmatch2}!!,
      field4    = this.plan!!.to${TypeEnum}(),
      field5    = this.request!!.${field4}!!.to${functionForConversion}(),
      ...
    )

  /**
   * Maps raw status string to enum representation.
   */
  private fun String.to${functionForConversion}(): ${functionForConversion} =
    when (this) {
      "Mapping2" -> ${functionForConversion}(this, ${functionForConversion}.Mapped.MAPPING1)
      // TODO: map other statuses
      else          -> ${functionForConversion}(this, ${functionForConversion}.Mapped.MAPPING3)
    }

  /**
   * Maps raw plan (${PlanType}) to type enum (${TypeEnum}).
   */
  private fun ${PlanType}.to${TypeEnum}(): ${TypeEnum} =
    ${TypeEnum}(
      specification2          = this.${variable1},
      specification3          = this.${variable1}!!,
      specification4          = ${DurationUnitEnum}.${Unit},
    )
}

