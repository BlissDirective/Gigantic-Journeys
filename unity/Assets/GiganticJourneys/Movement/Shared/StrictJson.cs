using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace GiganticJourneys.Movement
{
    /// <summary>
    /// A small strict JSON reader (RFC 8259) used by <see cref="MovementConfig"/>. Unity's
    /// JsonUtility silently ignores missing and unknown keys, which the movement contract
    /// forbids (M0-UNITY-03 AT-2), so the file is parsed into plain dictionaries first.
    /// Objects become <c>Dictionary&lt;string, object&gt;</c> (duplicate keys are an error),
    /// arrays <c>List&lt;object&gt;</c>, numbers <c>double</c>, plus <c>bool</c>, <c>string</c>
    /// and <c>null</c>.
    /// </summary>
    public static class StrictJson
    {
        public static object Parse(string text)
        {
            if (text == null)
                throw new FormatException("JSON text is null");
            var reader = new Reader(text);
            reader.SkipWhitespace();
            var value = reader.ReadValue();
            reader.SkipWhitespace();
            if (!reader.AtEnd)
                throw reader.Error("unexpected trailing characters");
            return value;
        }

        sealed class Reader
        {
            readonly string _s;
            int _i;

            public Reader(string s)
            {
                _s = s;
            }

            public bool AtEnd => _i >= _s.Length;

            public FormatException Error(string message) =>
                new FormatException($"JSON {message} at character {_i}");

            public void SkipWhitespace()
            {
                while (
                    !AtEnd && (_s[_i] == ' ' || _s[_i] == '\t' || _s[_i] == '\n' || _s[_i] == '\r')
                )
                    _i++;
            }

            char Peek() => AtEnd ? '\0' : _s[_i];

            void Expect(char c)
            {
                if (Peek() != c)
                    throw Error($"expected '{c}'");
                _i++;
            }

            public object ReadValue()
            {
                switch (Peek())
                {
                    case '{':
                        return ReadObject();
                    case '[':
                        return ReadArray();
                    case '"':
                        return ReadString();
                    case 't':
                        ReadLiteral("true");
                        return true;
                    case 'f':
                        ReadLiteral("false");
                        return false;
                    case 'n':
                        ReadLiteral("null");
                        return null;
                    default:
                        return ReadNumber();
                }
            }

            void ReadLiteral(string word)
            {
                if (string.CompareOrdinal(_s, _i, word, 0, word.Length) != 0)
                    throw Error($"expected '{word}'");
                _i += word.Length;
            }

            Dictionary<string, object> ReadObject()
            {
                Expect('{');
                var result = new Dictionary<string, object>(StringComparer.Ordinal);
                SkipWhitespace();
                if (Peek() == '}')
                {
                    _i++;
                    return result;
                }
                while (true)
                {
                    SkipWhitespace();
                    var key = ReadString();
                    SkipWhitespace();
                    Expect(':');
                    SkipWhitespace();
                    if (result.ContainsKey(key))
                        throw Error($"duplicate key '{key}'");
                    result[key] = ReadValue();
                    SkipWhitespace();
                    if (Peek() == ',')
                    {
                        _i++;
                        continue;
                    }
                    Expect('}');
                    return result;
                }
            }

            List<object> ReadArray()
            {
                Expect('[');
                var result = new List<object>();
                SkipWhitespace();
                if (Peek() == ']')
                {
                    _i++;
                    return result;
                }
                while (true)
                {
                    SkipWhitespace();
                    result.Add(ReadValue());
                    SkipWhitespace();
                    if (Peek() == ',')
                    {
                        _i++;
                        continue;
                    }
                    Expect(']');
                    return result;
                }
            }

            string ReadString()
            {
                Expect('"');
                var sb = new StringBuilder();
                while (true)
                {
                    if (AtEnd)
                        throw Error("unterminated string");
                    var c = _s[_i++];
                    if (c == '"')
                        return sb.ToString();
                    if (c != '\\')
                    {
                        sb.Append(c);
                        continue;
                    }
                    if (AtEnd)
                        throw Error("unterminated escape");
                    var e = _s[_i++];
                    switch (e)
                    {
                        case '"':
                        case '\\':
                        case '/':
                            sb.Append(e);
                            break;
                        case 'b':
                            sb.Append('\b');
                            break;
                        case 'f':
                            sb.Append('\f');
                            break;
                        case 'n':
                            sb.Append('\n');
                            break;
                        case 'r':
                            sb.Append('\r');
                            break;
                        case 't':
                            sb.Append('\t');
                            break;
                        case 'u':
                            if (_i + 4 > _s.Length)
                                throw Error("bad \\u escape");
                            sb.Append(
                                (char)
                                    int.Parse(
                                        _s.Substring(_i, 4),
                                        NumberStyles.HexNumber,
                                        CultureInfo.InvariantCulture
                                    )
                            );
                            _i += 4;
                            break;
                        default:
                            throw Error($"bad escape '\\{e}'");
                    }
                }
            }

            double ReadNumber()
            {
                var start = _i;
                if (Peek() == '-')
                    _i++;
                while (!AtEnd && "0123456789+-.eE".IndexOf(_s[_i]) >= 0)
                    _i++;
                if (start == _i)
                    throw Error("expected a value");
                var token = _s.Substring(start, _i - start);
                if (
                    !double.TryParse(
                        token,
                        NumberStyles.Float,
                        CultureInfo.InvariantCulture,
                        out var value
                    )
                )
                    throw Error($"bad number '{token}'");
                return value;
            }
        }
    }
}
