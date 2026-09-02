
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
  bool _simple = true;
  String? _flash;

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
    if (added == true) {
      setState(() => _flash = savedPlain);
      await _reload();
    }
  }

  Future<void> _export(Receipt r) async {
    final text = await _store.exportOne(r);
    if (!mounted) return;
    setState(() => _flash = 'Copied this receipt into a file you can keep.');
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Exported ${text.length} characters to the clipboard.')),
    );
  }

  Future<void> _import() async {
    final imported = await Navigator.of(context).push<Receipt>(
      MaterialPageRoute(builder: (_) => ImportPage(store: _store)),
    );
    if (imported != null) {
      setState(() => _flash = 'Imported a receipt. A receipt is not legal proof.');
      await _reload();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ForgeReceipts'),
        actions: [
          TextButton(
            onPressed: () => setState(() => _simple = !_simple),
            child: Text(_simple ? 'Simple' : 'Advanced'),
          ),
        ],
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
              'file with any court, Odyssey, or email. A receipt is not legal proof.',
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                FilledButton(
                  onPressed: _add,
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 14),
                    child: Text('Add file', style: TextStyle(fontSize: 20)),
                  ),
                ),
                const SizedBox(height: 8),
                OutlinedButton(
                  onPressed: _import,
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 14),
                    child: Text('Import receipt', style: TextStyle(fontSize: 18)),
                  ),
                ),
                const SizedBox(height: 8),
                OutlinedButton(
                  onPressed: _items.isEmpty ? null : () => _export(_items.first),
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 14),
                    child: Text('Export receipt', style: TextStyle(fontSize: 18)),
                  ),
                ),
              ],
            ),
          ),
          if (_flash != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                _flash!,
                style: const TextStyle(
                  color: kGold,
                  fontWeight: FontWeight.w700,
                ),
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
                                _simple
                                    ? '${r.kind}\n${r.hash.isEmpty ? r.id : r.hash}'
                                    : '${r.kind} · ${r.createdAt.toLocal()}\n${r.note}\n${r.hash}',
                              ),
                              isThreeLine: true,
                              onTap: () => Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => DetailPage(
                                    receipt: r,
                                    simple: _simple,
                                    onExport: () => _export(r),
                                  ),
                                ),
                              ),
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

class DetailPage extends StatelessWidget {
  const DetailPage({
    super.key,
    required this.receipt,
    required this.simple,
    required this.onExport,
  });

  final Receipt receipt;
  final bool simple;
  final VoidCallback onExport;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Receipt')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(notLegalAdvice),
          const SizedBox(height: 12),
          Text(receipt.summary, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          const Text('This is the saved receipt for this file.'),
          const SizedBox(height: 8),
          SelectableText(receipt.hash.isEmpty ? receipt.id : receipt.hash),
          if (!simple) ...[
            const SizedBox(height: 12),
            Text('kind: ${receipt.kind}'),
            Text('created: ${receipt.createdAt.toIso8601String()}'),
            Text(receipt.note),
            Text(receipt.childImpact),
            if (receipt.fileSha256.isNotEmpty) Text(receipt.fileSha256),
          ],
          const SizedBox(height: 20),
          FilledButton(
            onPressed: onExport,
            child: const Text('Export receipt'),
          ),
        ],
      ),
    );
  }
}

class ImportPage extends StatefulWidget {
  const ImportPage({super.key, required this.store});
  final ReceiptStore store;

  @override
  State<ImportPage> createState() => _ImportPageState();
}

class _ImportPageState extends State<ImportPage> {
  final _text = TextEditingController();
  String? _error;
  bool _working = false;

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  Future<void> _go() async {
    setState(() {
      _error = null;
      _working = true;
    });
    try {
      final r = await widget.store.importText(_text.text);
      if (!mounted) return;
      Navigator.of(context).pop(r);
    } on FormatException catch (e) {
      setState(() {
        _error = e.message;
        _working = false;
      });
    } catch (e) {
      setState(() {
        _error = 'That file is not valid JSON. Check commas and quotes, then try again.';
        _working = false;
      });
    }
  }

  Future<void> _paste() async {
    final data = await Clipboard.getData('text/plain');
    if (data?.text != null) setState(() => _text.text = data!.text!);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Import receipt')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(notLegalAdvice),
          const SizedBox(height: 12),
          const Text('Paste a receipt JSON file. This stays on this phone.'),
          const SizedBox(height: 12),
          TextField(
            controller: _text,
            maxLines: 10,
            decoration: const InputDecoration(labelText: 'Receipt JSON'),
          ),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: _paste, child: const Text('Paste')),
          const SizedBox(height: 8),
          FilledButton(
            onPressed: _working ? null : _go,
            child: const Text('Import receipt'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Color(0xFFB54A4A))),
          ],
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
      appBar: AppBar(title: const Text('Add file')),
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
