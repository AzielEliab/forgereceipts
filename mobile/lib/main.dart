import 'package:flutter/material.dart';

import 'store.dart';
import 'theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ForgeReceiptsApp());
}

class ForgeReceiptsApp extends StatelessWidget {
  const ForgeReceiptsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ForgeReceipts',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: const ListPage(),
    );
  }
}

class ListPage extends StatefulWidget {
  const ListPage({super.key});

  @override
  State<ListPage> createState() => _ListPageState();
}

class _ListPageState extends State<ListPage> {
  final _store = ReceiptStore();
  List<Receipt> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    final items = await _store.load();
    if (!mounted) return;
    setState(() {
      _items = items;
      _loading = false;
    });
  }

  Future<void> _add() async {
    final added = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => AddPage(store: _store)),
    );
    if (added == true) await _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ForgeReceipts')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _add,
        icon: const Icon(Icons.note_add),
        label: const Text('Add note'),
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            color: const Color(0x33C9A227),
            padding: const EdgeInsets.all(12),
            child: const Text(
              notLegalAdvice,
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Text(
              motto,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: kGold,
                    fontStyle: FontStyle.italic,
                  ),
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              'On-device list only. Nothing is uploaded. This app does not '
              'file with any court, Odyssey, or email.',
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _items.isEmpty
                    ? const Center(child: Text('No receipts yet.'))
                    : ListView.builder(
                        itemCount: _items.length,
                        itemBuilder: (context, i) {
                          final r = _items[i];
                          return Card(
                            margin: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 6,
                            ),
                            child: ListTile(
                              title: Text(r.summary),
                              subtitle: Text(
                                '${r.kind} · ${r.createdAt.toLocal()}\n${r.note}',
                              ),
                              isThreeLine: true,
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}

class AddPage extends StatefulWidget {
  const AddPage({super.key, required this.store});
  final ReceiptStore store;

  @override
  State<AddPage> createState() => _AddPageState();
}

class _AddPageState extends State<AddPage> {
  final _summary = TextEditingController();
  final _note = TextEditingController();
  final _child = TextEditingController();
  String _kind = 'incident';
  bool _saving = false;

  @override
  void dispose() {
    _summary.dispose();
    _note.dispose();
    _child.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_summary.text.trim().isEmpty) return;
    setState(() => _saving = true);
    final r = Receipt(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      createdAt: DateTime.now().toUtc(),
      summary: _summary.text.trim(),
      note: _note.text.trim(),
      kind: _kind,
      childImpact: _child.text.trim(),
    );
    await widget.store.add(r);
    if (!mounted) return;
    Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add note')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(notLegalAdvice),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _kind,
            items: const [
              DropdownMenuItem(value: 'incident', child: Text('Incident')),
              DropdownMenuItem(value: 'journal', child: Text('Time with child')),
              DropdownMenuItem(value: 'forensics', child: Text('Forensics note')),
            ],
            onChanged: (v) => setState(() => _kind = v ?? 'incident'),
            decoration: const InputDecoration(labelText: 'Kind'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _summary,
            decoration: const InputDecoration(labelText: 'Summary'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _note,
            maxLines: 4,
            decoration: const InputDecoration(labelText: 'Private note'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _child,
            decoration: const InputDecoration(
              labelText: 'Child impact (hashed on desktop; local here)',
            ),
          ),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: const Text('Save on this device'),
          ),
        ],
      ),
    );
  }
}
