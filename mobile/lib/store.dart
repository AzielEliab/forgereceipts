import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

const motto =
    "Child's Best Interests First. Integrity Over Narrative. Local Control. Always.";

const notLegalAdvice =
    'Not legal advice. This software does not practice law, does not '
    'guarantee any court outcome, and does not contact any court. No '
    'filing. Consult a licensed attorney in your jurisdiction.';

class Receipt {
  Receipt({
    required this.id,
    required this.createdAt,
    required this.summary,
    required this.note,
    this.kind = 'incident',
    this.childImpact = '',
  });

  final String id;
  final DateTime createdAt;
  final String summary;
  final String note;
  final String kind;
  final String childImpact;

  Map<String, Object> toJson() => {
        'id': id,
        'createdAt': createdAt.toIso8601String(),
        'summary': summary,
        'note': note,
        'kind': kind,
        'childImpact': childImpact,
      };

  static Receipt fromJson(Map<String, dynamic> m) => Receipt(
        id: m['id'] as String? ?? '',
        createdAt: DateTime.tryParse(m['createdAt'] as String? ?? '') ??
            DateTime.fromMillisecondsSinceEpoch(0),
        summary: m['summary'] as String? ?? '',
        note: m['note'] as String? ?? '',
        kind: m['kind'] as String? ?? 'incident',
        childImpact: m['childImpact'] as String? ?? '',
      );
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
}
