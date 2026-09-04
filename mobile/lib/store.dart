
import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

const motto =
    "Child's Best Interests First. Integrity Over Narrative. Local Control. Always.";

const notLegalAdvice =
    'Not legal advice. A receipt is not legal proof. This software does not '
    'practice law, does not guarantee any court outcome, and does not contact '
    'any court. No filing. Consult a licensed attorney in your jurisdiction.';

const receiptFormat = 'forgereceipts.receipt/v1';
const productVersion = '0.3.0';
const savedPlain = 'Saved a receipt for this file';

class Receipt {
  Receipt({
    required this.id,
    required this.createdAt,
    required this.summary,
    required this.note,
    this.kind = 'incident',
    this.childImpact = '',
    this.hash = '',
    this.fileName = '',
    this.fileSha256 = '',
  });

  final String id;
  final DateTime createdAt;
  final String summary;
  final String note;
  final String kind;
  final String childImpact;
  final String hash;
  final String fileName;
  final String fileSha256;

  Map<String, Object> toJson() => {
        'id': id,
        'createdAt': createdAt.toIso8601String(),
        'timestamp': createdAt.toIso8601String(),
        'summary': summary,
        'note': note,
        'kind': kind,
        'childImpact': childImpact,
        'child_impact': childImpact,
        'hash': hash,
        'file_name': fileName,
        'file_sha256': fileSha256,
      };

  static Receipt fromJson(Map<String, dynamic> m) => Receipt(
        id: m['id'] as String? ?? m['hash'] as String? ?? '',
        createdAt: DateTime.tryParse(
              (m['createdAt'] ?? m['timestamp']) as String? ?? '',
            ) ??
            DateTime.fromMillisecondsSinceEpoch(0),
        summary: m['summary'] as String? ?? '',
        note: m['note'] as String? ?? m['evidence'] as String? ?? '',
        kind: m['kind'] as String? ?? 'incident',
        childImpact:
            m['childImpact'] as String? ?? m['child_impact'] as String? ?? '',
        hash: m['hash'] as String? ?? '',
        fileName: m['file_name'] as String? ?? m['fileName'] as String? ?? '',
        fileSha256:
            m['file_sha256'] as String? ?? m['fileSha256'] as String? ?? '',
      );

  String exportEnvelope() {
    final envelope = <String, Object>{
      'format': receiptFormat,
      'product': 'forgereceipts',
      'product_version': productVersion,
      'disclaimer': notLegalAdvice,
      'not_legal_advice': true,
      'not_legal_proof': true,
      'receipt': toJson(),
    };
    return const JsonEncoder.withIndent('  ').convert(envelope);
  }

  static Receipt importEnvelope(String raw) {
    late final Object? decoded;
    try {
      decoded = jsonDecode(raw);
    } on FormatException {
      throw const FormatException(
        'That file is not valid JSON. Check commas and quotes, then try again.',
      );
    }
    if (decoded is! Map) {
      throw const FormatException(
        'That JSON is not a receipt object. It must be a set of named fields inside { }.',
      );
    }
    final map = Map<String, dynamic>.from(decoded);
    final rec = map['receipt'] ?? map;
    if (rec is! Map) {
      throw const FormatException(
        'No receipt was found in that file. Export a receipt and try again.',
      );
    }
    return Receipt.fromJson(Map<String, dynamic>.from(rec));
  }
}

class ReceiptStore {
  static const _key = 'forgereceipts.receipts.v1';

  Future<List<Receipt>> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null || raw.isEmpty) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list
        .map((e) => Receipt.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList()
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
  }

  Future<void> add(Receipt r) async {
    final all = await load();
    all.insert(0, r);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _key,
      jsonEncode(all.map((e) => e.toJson()).toList()),
    );
  }

  Future<String> exportOne(Receipt r) async {
    final text = r.exportEnvelope();
    await Clipboard.setData(ClipboardData(text: text));
    return text;
  }

  Future<Receipt> importText(String raw) async {
    final r = Receipt.importEnvelope(raw);
    await add(r);
    return r;
  }
}
